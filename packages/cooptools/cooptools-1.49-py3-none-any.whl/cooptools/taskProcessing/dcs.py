from dataclasses import dataclass, asdict, field
from typing import List, Iterable, Dict, Any, Protocol
import datetime
from cooptools import typevalidation as tv
import json
import cooptools.date_utils as du
from cooptools.coopEnum import CoopEnum
from cooptools.protocols import UniqueIdentifier
from cooptools import materialHandling as mh
from cooptools import coopDataclass as cdc
from cooptools import typeProviders as tp
import pprint
from typing import Callable
from cooptools import common as cmn
from cooptools import qualifiers as qual

UNDEFINED = 'UNDEFINED'


class TaskLinkType(CoopEnum):
    PREDECESSOR = 'predecessor'
    PARENT = 'parent'


class InstructionPayloadProtocol(Protocol):
    pass


class CriteriaPayloadProtocol(Protocol):
    def resolve_instruction_payload(cls) -> InstructionPayloadProtocol:
        pass


@dataclass(frozen=True, slots=True, kw_only=True)
class TaskLink(cdc.BaseDataClass):
    task_link_type: TaskLinkType
    linked_task_id: str

    def __post_init__(self):
        if type(self.task_link_type) == str:
            object.__setattr__(self, f'{self.task_link_type=}'.split('=')[0].replace('self.', ''),
                               TaskLinkType.from_str(self.task_link_type))


TaskLinkProvider = Callable[[], TaskLink] | TaskLink


@dataclass(frozen=True, slots=True, kw_only=True)
class PredecessorTaskLink(TaskLink):
    task_link_type: TaskLinkType = field(init=False, default=TaskLinkType.PREDECESSOR)
    require_same_agent: bool = False
    prevent_intermediate_tasks: bool = False

    def __post_init__(self):
        super(PredecessorTaskLink, self).__post_init__()


@dataclass(frozen=True, slots=True, kw_only=True)
class ExecutionCriteria(cdc.BaseDataClass):
    criteria_payload: CriteriaPayloadProtocol = field(default_factory=dict)
    required_agent_id_options: Iterable[str] = field(default_factory=list)
    required_agent_type_options: Iterable[str] = field(default_factory=list)
    instruction_payload_resolution_args: Dict = field(default_factory=dict)
    criteria_payload_type: str = field(default=None, repr=False)
    _instruction_payload: InstructionPayloadProtocol = field(default=None)

    def __post_init__(self):
        if self.criteria_payload_type is None:
            object.__setattr__(self, 'criteria_payload_type', str(type(self.criteria_payload)))

    def instruction_payload(self,
                            invalidate: bool = False):
        if invalidate:
            object.__setattr__(self, '_instruction_payload', None)

        if self._instruction_payload is None:
            ip = self.criteria_payload.resolve_instruction_payload()

            object.__setattr__(self, '_instruction_payload', ip)

        return self._instruction_payload


@dataclass(frozen=True, slots=True, kw_only=True)
class HeirarchyCriteria(cdc.BaseDataClass):
    task_group_id: UniqueIdentifier = field(default=UNDEFINED)
    task_links: Iterable[TaskLink] = field(default_factory=list)

    def __post_init__(self):
        if self.task_group_id in [None, '']:
            object.__setattr__(self, 'task_group_id', UNDEFINED)

        tdy = 'TODAY'
        value = str(du.date_to_condensed_string(
            du.today(remove_hrs=True, remove_min=True, remove_sec=True, remove_ms=True)))
        if self.task_group_id.upper().strip() == tdy:
            object.__setattr__(self, 'task_group_id', value)

        object.__setattr__(self, 'task_group_id', cmn.case_insensitive_replace(self.task_group_id,
                                                                               f"<{tdy}>",
                                                                               value
                                                                               )
                           )


@dataclass(frozen=True, slots=True, kw_only=True)
class TaskMeta(cdc.BaseDataClass):
    task_type: str
    creating_user_id: UniqueIdentifier = field(default=UNDEFINED)
    created_date: datetime.datetime = field(default_factory=du.now)
    due_date: datetime.datetime = None
    expiration_date: datetime.datetime = None
    priority: int = 999

    def __post_init__(self):
        object.__setattr__(self, f'{self.due_date=}'.split('=')[0].replace('self.', ''),
                           tv.datestamp_tryParse(self.due_date))
        object.__setattr__(self, f'{self.created_date=}'.split('=')[0].replace('self.', ''),
                           tv.datestamp_tryParse(self.created_date))
        object.__setattr__(self, f'{self.expiration_date=}'.split('=')[0].replace('self.', ''),
                           tv.datestamp_tryParse(self.expiration_date))
        if type(self.priority) == str:
            object.__setattr__(self, f'{self.priority=}'.split('=')[0].replace('self.', ''), int(self.priority))

    def toJson(self):
        return json.dumps(asdict(self), default=str, indent=4)


@dataclass(frozen=True, slots=True, kw_only=True)
class Task(cdc.BaseIdentifiedDataClass):
    meta: TaskMeta
    execution_criteria: ExecutionCriteria
    heirarchy_criteria: HeirarchyCriteria = field(default_factory=HeirarchyCriteria)

    def __post_init__(self):
        if type(self.meta) == dict:
            object.__setattr__(self, f'{self.meta=}'.replace('self.', '').split('=')[0], TaskMeta(**self.meta))

        if type(self.execution_criteria) == dict:
            object.__setattr__(self, f'{self.execution_criteria=}'.replace('self.', '').split('=')[0],
                               ExecutionCriteria(**self.execution_criteria))

        if type(self.heirarchy_criteria) == dict:
            object.__setattr__(self, f'{self.heirarchy_criteria=}'.replace('self.', '').split('=')[0],
                               HeirarchyCriteria(**self.heirarchy_criteria))


@dataclass(frozen=True, slots=True, kw_only=True)
class MissionInstructionPayload(InstructionPayloadProtocol, cdc.BaseDataClass):
    task_names: Iterable[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class MissionCriteriaPayload(CriteriaPayloadProtocol, cdc.BaseDataClass):
    task_names: Iterable[str]

    def resolve_instruction_payload(self,
                                    ) -> MissionInstructionPayload:
        return MissionInstructionPayload(
            task_names=self.task_names
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class MoveInstructionPayload(InstructionPayloadProtocol, cdc.BaseDataClass):
    waypoints: Iterable[str]


@dataclass(frozen=True, slots=True, kw_only=True)
class MoveCriteriaPayload(CriteriaPayloadProtocol, cdc.BaseDataClass):
    waypoints: Iterable[str]

    def resolve_instruction_payload(self,
                                    ) -> MoveInstructionPayload:
        return MoveInstructionPayload(
            waypoints=self.waypoints
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadTransferInstructionPayload(InstructionPayloadProtocol, cdc.BaseDataClass):
    load_meta: mh.Load
    agent_payload_position_id: str = field(default='1')
    source_loc: mh.Location
    dest_loc: mh.Location

    def short_str(self):
        cntnr_txt = ""
        if self.load_meta is not None:
            cntnr_txt = f"[{self.load_meta.id}] "

        return f"{cntnr_txt}{self.source_loc.id}->{self.dest_loc.id}"


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadTransferCriteriaPayload(CriteriaPayloadProtocol, cdc.BaseDataClass):
    load_qualifier: mh.LoadQualifier | mh.Load
    agent_payload_position_id: str = field(default='1')
    source_loc_qualifier: mh.LocationQualifier | mh.Location
    dest_loc_qualifier: mh.LocationQualifier | mh.Location
    load_list_provider: mh.LoadListProvider = None
    source_location_list_provider: mh.LocationListProvider = None
    dest_location_list_provider: mh.LocationListProvider = None

    @classmethod
    def from_vals(cls,
                  source_loc: tp.StringProvider | mh.Location,
                  dest_loc: tp.StringProvider | mh.Location,
                  load: tp.StringProvider | mh.Load):

        if type(load) != mh.Load:
            load = mh.Load(id=tp.resolve(load))

        if type(dest_loc) != mh.Location:
            dest_loc = mh.Location(id=tp.resolve(dest_loc))

        if type(source_loc) != mh.Location:
            source_loc = mh.Location(id=tp.resolve(source_loc))

        return LoadTransferCriteriaPayload(
            load_qualifier=mh.LoadQualifier(
                load=load
            ),
            source_loc_qualifier=mh.LocationQualifier(
                id_qualifier=qual.PatternMatchQualifier(id=source_loc.id)
            ),
            dest_loc_qualifier=mh.LocationQualifier(
                id_qualifier=qual.PatternMatchQualifier(id=dest_loc.id)
            ),
            load_list_provider=[load],
            source_location_list_provider=[source_loc],
            dest_location_list_provider=[dest_loc]
        )

    def __post_init__(self):
        # ensure container type is a string
        if type(self.load_qualifier) == dict:
            object.__setattr__(self, f'{self.load_qualifier=}'.replace('self.', '').split('=')[0],
                               mh.LoadQualifier(**self.load_qualifier))
        if type(self.source_loc_qualifier) == dict:
            object.__setattr__(self, f'{self.source_loc_qualifier=}'.split('=')[0].replace('self.', ''),
                               mh.LocationQualifier(**self.source_loc_qualifier))
        if type(self.dest_loc_qualifier) == dict:
            object.__setattr__(self, f'{self.dest_loc_qualifier=}'.split('=')[0].replace('self.', ''),
                               mh.LocationQualifier(**self.dest_loc_qualifier))
        if self.agent_payload_position_id is None:
            object.__setattr__(self, f'{self.agent_payload_position_id=}'.split('=')[0].replace('self.', ''), '1')

    def resolve_instruction_payload(self) -> LoadTransferInstructionPayload:

        if self.source_location_list_provider is None:
            raise ValueError(f"Unable to resolve instruction payload: source_location_list_provider was not provided")
        if self.dest_location_list_provider is None:
            raise ValueError(f"Unable to resolve instruction payload: dest_location_list_provider was not provided")
        if self.load_list_provider is None:
            raise ValueError(f"Unable to resolve instruction payload: load_list_provider was not provided")

        # resolve source location
        source_location_dict = {x.id: x for x in tp.resolve(self.source_location_list_provider)}

        if type(self.source_loc_qualifier) == mh.Location:
            source = self.source_loc_qualifier
        elif type(self.source_loc_qualifier) == mh.LocationQualifier:
            qualifying_locs = [k for k, v in self.source_loc_qualifier.qualify(source_location_dict.values()).items() if
                               v.result is True]

            if len(qualifying_locs) == 0:
                raise ValueError(
                    f"None of the locations {source_location_dict} qualified according to  {self.source_loc_qualifier}")

            source = qualifying_locs[0]
        else:
            raise ValueError(f"Unable to resolve source location")

        # resolve destination location
        dest_location_dict = {x.id: x for x in tp.resolve(self.dest_location_list_provider)}
        if type(self.dest_loc_qualifier) == mh.Location:
            dest = self.dest_loc_qualifier
        elif type(self.dest_loc_qualifier) == mh.LocationQualifier:
            qualifying_locs = [k for k, v in self.dest_loc_qualifier.qualify(dest_location_dict.values()).items() if
                               v.result is True]

            if len(qualifying_locs) == 0:
                raise ValueError(
                    f"None of the locations {source_location_dict} qualified according to {self.source_loc_qualifier}")

            dest = qualifying_locs[0]
        else:
            raise ValueError(f"Unable to resolve dest location")

        # resolve load
        load_dict = {x.id: x for x in tp.resolve(self.load_list_provider)}

        if type(self.load_qualifier) == mh.Load:
            load = self.load_qualifier
        else:
            qualify_loads = self.load_qualifier.qualify(load_dict.values())
            qualifying_loads = [k for k, v in qualify_loads.items() if v.result is True]
            if len(qualifying_loads) == 0:
                raise ValueError(f"No loads qualified according to the qualifier: \n{pprint.pformat(qualify_loads)}")

            # TODO: This should be updated to evaluate based on some criteria
            load = load_dict[qualifying_loads[0]]

        return LoadTransferInstructionPayload(
            load_meta=load,
            agent_payload_position_id=self.agent_payload_position_id,
            source_loc=source_location_dict[source],
            dest_loc=dest_location_dict[dest]
        )


def load_transfer_task(
        tg_name: tp.StringProvider,
        task_name: tp.StringProvider,
        load: tp.StringProvider | mh.Load,
        source_loc: tp.StringProvider | mh.Location,
        task_type: tp.StringProvider,
        dest_loc: tp.StringProvider | mh.Location = None,
        dest_loc_pattern: tp.StringProvider = None,
        predecessor_tasks: Iterable[Task] = None,
        creating_user_id: tp.StringProvider = "DEFAULT_USER"
):
    if dest_loc is None and dest_loc_pattern is None:
        raise ValueError

    if dest_loc_pattern is not None:
        raise NotImplementedError()

    return Task(
        id=tp.resolve(task_name),
        meta=TaskMeta(
            task_type=tp.resolve(task_type),
            creating_user_id=tp.resolve(creating_user_id),
        ),
        execution_criteria=ExecutionCriteria(
            criteria_payload=LoadTransferCriteriaPayload.from_vals(
                load=load,
                source_loc=source_loc,
                dest_loc=dest_loc
            ),
        ),
        heirarchy_criteria=HeirarchyCriteria(
            task_group_id=tp.resolve(tg_name),
            task_links=[
                PredecessorTaskLink(
                    linked_task_id=x.id
                ) for x in predecessor_tasks
            ]
        ),
    )


if __name__ == '__main__':
    from pprint import pprint
    from dataclasses import replace

    meta_1 = TaskMeta(
        task_type="user type 1",
    )
    meta_2 = TaskMeta(
        task_type="user type 2",
    )


    def test_base_args():
        task = Task(
            meta=meta_1,
            execution_criteria=ExecutionCriteria(
                criteria_payload=MissionCriteriaPayload(
                    task_names=['2', '3', '4'],
                ),
            )
        )
        pprint(task)


    def test_replace():
        task = Task(
            meta=meta_1,
            execution_criteria=ExecutionCriteria(
                criteria_payload=MissionCriteriaPayload(
                    task_names=['2', '3', '4'],
                ),
            )
        )

        task = replace(task,
                       meta=meta_2)

        pprint(task)


    def test_to_json():
        task = Task(
            meta=meta_1,
            execution_criteria=ExecutionCriteria(
                criteria_payload=MissionCriteriaPayload(
                    task_names=['2', '3', '4'],
                ),
            )
        )

        j = task.to_json()
        pprint(j)

        pprint(Task(**json.loads(j)))


    def test_resolve_instruction_payload():
        task = Task(
            meta=meta_1,
            execution_criteria=ExecutionCriteria(
                criteria_payload=LoadTransferCriteriaPayload(
                    load_qualifier=mh.LoadQualifier(),
                    source_loc_qualifier=mh.LocationQualifier(),
                    dest_loc_qualifier=mh.LocationQualifier()
                ),
            )
        )

        cp: LoadTransferCriteriaPayload = task.execution_criteria.criteria_payload

        locs = [mh.Location(id=f'Loc{x}') for x in range(10)]
        loads = [mh.Load(id=f'Load{x}') for x in range(10)]
        instructions = cp.resolve_instruction_payload(
            location_list_provider=locs,
            load_list_provider=loads,
        )

        pprint(instructions)


    def test_heirarcy_obj():
        hc = HeirarchyCriteria(
            task_group_id='TODAY'
        )
        pprint(hc)


    # test_base_args()
    # test_replace()
    # test_to_json()
    # test_resolve_instruction_payload()
    test_heirarcy_obj()