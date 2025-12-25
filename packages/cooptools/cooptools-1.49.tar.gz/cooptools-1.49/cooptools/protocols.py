from typing import Protocol, Dict, runtime_checkable
import uuid

UniqueIdentifier = str | uuid.UUID | int

@runtime_checkable
class IdentifiableProtocol(Protocol):
    def get_id(self) -> UniqueIdentifier:
        pass

@runtime_checkable
class ComparableProtocol(Protocol):
    def __lt__(self, other):
        pass

    def __gt__(self, other):
        pass

    def __eq__(self, other):
        pass

    def __ge__(self, other):
        pass

    def __le__(self, other):
        pass

    def __ne__(self, other):
        pass

@runtime_checkable
class DictableProtocol(Protocol):
    def to_dict(self) -> Dict:
        raise NotImplementedError()

@runtime_checkable
class JsonableDictProtocol(Protocol):
    def to_jsonable_dict(self) -> Dict:
        raise NotImplementedError()

@runtime_checkable
class JsonableProtocol(Protocol):
    def to_json(self) -> str:
        raise NotImplementedError()
