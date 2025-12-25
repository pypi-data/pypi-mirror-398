import datetime
import uuid
from dataclasses import dataclass, field, asdict
from cooptools.coopEnum import CoopEnum, auto
import cooptools.date_utils as du
from typing import Iterable

class ActionItemPriority(CoopEnum):
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()

class ActionItemStatus(CoopEnum):
    PROPOSED = auto()
    APPROVED = auto()
    ACTIVE = auto()
    BLOCKED = auto()
    RESOLVED = auto()
    REMOVED = auto()

class ActionItemCategory(CoopEnum):
    FAILED_REQUIREMENT = auto()
    MISSED_REQUIREMENT = auto()
    NEW_REQUEST = auto()
    ENHANCEMENT = auto()

@dataclass(frozen=True, slots=True)
class Comment:
    who: str
    text: str
    date_stamp: datetime.datetime = None

    def __post_init__(self):
        if self.date_stamp is None:
            object.__setattr__(self, f'{self.date_stamp=}'.split('=')[0].replace('self.', ''), du.now())

    def __str__(self):
        return f"{du.date_to_condensed_string(self.date_stamp)} [{self.who}] - {self.text}"

@dataclass(frozen=True, slots=True)
class ActionItemMeta:
    priority: ActionItemPriority = None
    status: ActionItemStatus = None
    category: ActionItemCategory = None
    identified_by: str = None
    owner: str = None
    associated_wi: str = None


    def with_(
            self,
            args,
    ):
        obj_dict = asdict(self)
        update_dict = {k: v for k, v in asdict(args).items() if v is not None}

        obj_dict.update(update_dict)
        return ActionItemMeta(**obj_dict)


@dataclass(frozen=True, slots=True)
class ActionItem:
    meta: ActionItemMeta
    description: str
    id: str = None
    recorded_date_stamp: datetime.datetime = None
    comments: frozenset[Comment] = field(default_factory=frozenset)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return hash(other) == self.__hash__()

    def __post_init__(self):
        if self.recorded_date_stamp is None:
            object.__setattr__(self, f'{self.recorded_date_stamp=}'.split('=')[0].replace('self.', ''), du.now())

        if self.id is None:
            object.__setattr__(self, f'{self.id=}'.split('=')[0].replace('self.', ''), str(uuid.uuid4()))

    def with_(
            self,
            meta_updates: ActionItemMeta = None,
            meta_override: ActionItemMeta = None,
            added_comments: Iterable[Comment] = None,
            updated_description: str = None
    ):
        updated_meta = None
        if meta_updates is not None:
            updated_meta = self.meta.with_(meta_updates)

        new_comments = self.comments
        if added_comments is not None:
            new_comments = frozenset(list(self.comments) + list(added_comments))

        new_description = self.description
        if updated_description is not None:
            new_description = updated_description

        if meta_override is not None:
            updated_meta = meta_override

        return ActionItem(
            id=self.id,
            recorded_date_stamp=self.recorded_date_stamp,
            meta=updated_meta,
            comments=new_comments,
            description=new_description
        )

if __name__ == "__main__":
    from pprint import pprint


    ai = ActionItem(
        meta=ActionItemMeta(
            priority=ActionItemPriority.HIGH,
            status=ActionItemStatus.ACTIVE,
            category=ActionItemCategory.NEW_REQUEST
        )
    )

    pprint(ai)

    ai2 = ai.with_(
        meta_updates=ActionItemMeta(
            owner='MAZZO'
        ),
        added_comments=[
            Comment(who='me', text="my comment", date_stamp=datetime.datetime.now())
        ]
    )
    pprint(ai2)