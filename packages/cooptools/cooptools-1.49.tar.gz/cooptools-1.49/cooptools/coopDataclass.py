from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Union, Tuple, Iterable, Self, Any
import uuid
from cooptools.protocols import UniqueIdentifier
import json

def case_insensitive_initializer(model: Any, **kwargs):

    case_insensitive_dict = {var.upper(): var for var in model.__dataclass_fields__}

    ret = {
        case_insensitive_dict[k.upper()]: v for k, v in kwargs.items()
    }

    return model(**ret)


@dataclass(frozen=True, slots=True)
class BaseDataClass:
    details: Optional[Dict] = field(default_factory=dict)

    @classmethod
    def case_insensitive_init(cls, **kwargs):
        return case_insensitive_initializer(
            cls,
            **kwargs
        )

    def to_json(self):
        return json.dumps(asdict(self), default=str, indent=4)


@dataclass(frozen=True, slots=True)
class BaseIdentifiedDataClass(BaseDataClass):
    id: Optional[UniqueIdentifier] = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        if self.id is None:
            object.__setattr__(self, 'id', uuid.uuid4())

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return hash(other) == hash(self)

    def get_id(self):
        return self.id
