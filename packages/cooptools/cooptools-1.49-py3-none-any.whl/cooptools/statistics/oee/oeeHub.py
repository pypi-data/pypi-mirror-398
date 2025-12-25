import datetime
import time
import uuid
from dataclasses import dataclass, field
from typing import Iterable, Dict, List, Tuple

@dataclass(frozen=True, slots=True)
class Defect:
    name: str

@dataclass(frozen=True, slots=True)
class PhaseMeta:
    name: str
    applicable_defects: Iterable[Defect] = None

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(other) == hash(self)

@dataclass(frozen=True, slots=True)
class PhaseRelationship:
    phase: PhaseMeta
    sub_phases: Iterable[PhaseMeta]

@dataclass(frozen=True, slots=True)
class Span:
    start: datetime.datetime
    end: datetime.datetime = None

    def with_end(self,
                 date_stamp: datetime.datetime = None):
        if date_stamp is None:
            date_stamp = datetime.datetime.now()

        return Span(
            start=self.start,
            end=date_stamp
        )

    @property
    def DeltaSeconds(self):
        if self.end is None:
            return None

        return (self.end - self.start).seconds

@dataclass(frozen=True, slots=True)
class ProcessMeta:
    name: str
    phase_heirarchy: Iterable[PhaseRelationship]

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(other) == hash(self)

    @property
    def Phases(self) -> List[PhaseMeta]:
        ret = []
        for pr in self.phase_heirarchy:
            ret.append(pr.phase)
            ret += pr.sub_phases
        return list(set(ret))

class ProcessInstance:

    def __init__(self,
                 id: uuid.UUID,
                 meta: ProcessMeta):
        self.id: uuid.UUID = id
        self.meta: ProcessMeta = meta
        self.phase_spans: Dict[PhaseMeta, Span] = {}


    def start_phase(self,
                    phase: PhaseMeta,
                    start_stamp: datetime.datetime = None):
        if phase not in self.meta.Phases:
            raise ValueError(f"The input phase [{phase}] is not part of the process meta [{self.meta}]")

        if phase in self.phase_spans.keys():
            raise ValueError(f"The input phase to be started [{phase}] has already been started")


        if start_stamp is None:
            start_stamp = datetime.datetime.now()

        self.phase_spans[phase] = Span(start=start_stamp)

    def end_phase(self,
                  phase: PhaseMeta,
                  end_stamp: datetime.datetime = None):
        if phase not in self.meta.Phases:
            raise ValueError(f"The input phase [{phase}] is not part of the process meta [{self.meta}]")

        if phase not in self.phase_spans.keys():
            raise ValueError(f"The input phase to be ended [{phase}] has not been started")

        if end_stamp is None:
            end_stamp = datetime.datetime.now()

        self.phase_spans[phase] = self.phase_spans[phase].with_end(date_stamp=end_stamp)


class OeeProcessManager:
    def __init__(self):
        self.process_instances: Dict[uuid.UUID, ProcessInstance] = {}

    def start_process(self,
                      meta: ProcessMeta,
                      phase: PhaseMeta = None,
                      date_stamp: datetime.datetime = None
                      ):
        process_id = uuid.uuid4()
        new_instance = ProcessInstance(
            id=process_id,
            meta=meta,
        )
        self.process_instances[process_id] = new_instance

        if phase is not None:
            new_instance.start_phase(
                phase=phase,
                start_stamp=date_stamp
            )
        return new_instance

    def start_incident(self):
        pass

    def end_incident(self):
        pass

    def record_defect(self):
        pass

    @property
    def SpansByProcessPhase(self) -> Dict[Tuple[ProcessMeta, PhaseMeta], List[Span]]:
        ret = {}

        for pid, process_instance in self.process_instances.items():
            for phase, span in process_instance.phase_spans.items():
                k = tuple((process_instance.meta, phase))
                ret.setdefault(k, [])
                ret[k].append(span)

        return ret

if __name__ == '__main__':
    from cooptools.coopEnum import CoopEnum, auto

    class LoadTransferPhase(CoopEnum):
        LOAD_WAITS = auto()
        LOAD_WAITS_PICK_ASSIGN = auto()
        LOAD_WAITS_AGENT_MOVE = auto()
        LOAD_WAITS_PREP_FOR_PICK = auto()


    load_wait_phase = PhaseMeta(
        name=LoadTransferPhase.LOAD_WAITS.name
    )
    load_wait_pick_assign = PhaseMeta(
        name=LoadTransferPhase.LOAD_WAITS_PICK_ASSIGN.name
    )
    load_wait_agent_move = PhaseMeta(
        name=LoadTransferPhase.LOAD_WAITS_AGENT_MOVE.name
    )
    load_wait_prep_for_pick = PhaseMeta(
        name=LoadTransferPhase.LOAD_WAITS_PREP_FOR_PICK.name
    )

    load_wait = PhaseRelationship(
        phase=load_wait_phase,
        sub_phases=[
            load_wait_pick_assign,
            load_wait_agent_move,
            load_wait_prep_for_pick
        ]
    )


    load_transfer = ProcessMeta(
        name='load_transfer',
        phase_heirarchy=[load_wait],
    )


    oee = OeeProcessManager()

    import random as rnd

    for ii in range(100):
        start = datetime.datetime.now()
        lt1 = oee.start_process(
            meta=load_transfer,
            phase=load_wait_phase,
        )
        lt1.end_phase(
            phase=load_wait_phase,
            end_stamp=start + datetime.timedelta(seconds=rnd.randint(1, 10))
        )

    import pprint

    for k, v in oee.process_instances.items():
        pprint.pprint(v.phase_spans)

    from cooptools.statistics.controlChart.controlChart import control
    # from cooptools.statistics.controlChart.plotting import plot_control_chart
    import pandas as pd
    # import matplotlib.pyplot as plt
    import cooptools.pandasHelpers as ph

    for pp, spans in oee.SpansByProcessPhase.items():
        process, phase = pp

        control_data = control([x.DeltaSeconds for x in spans], trailing_window=10)
        cc_df = pd.DataFrame(control_data)
        ph.pretty_print_dataframe(cc_df)
        # f, axes = plt.subplots(1, 1, figsize=(15, 10))
        # plot_control_chart(control_data, axes, trailing_window=10)
        # plt.show()


