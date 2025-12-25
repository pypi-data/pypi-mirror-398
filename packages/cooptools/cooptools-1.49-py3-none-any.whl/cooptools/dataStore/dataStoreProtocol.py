import json
import uuid
from typing import Protocol, Iterable, Tuple, Dict, Self
import logging
from cooptools.protocols import IdentifiableProtocol, UniqueIdentifier
from cooptools.qualifiers.qualifier import PatternMatchQualifier

logger = logging.getLogger(__name__)

StorableData = IdentifiableProtocol | Dict | str
SUPPORTED_IDENTIFIERS = ['id', '_id', "obj_id", "obj", "name", "Id", "ID"]

class ItemAlreadyInStoreException(Exception):
    def __init__(self, item: IdentifiableProtocol):
        err = f"item {item.get_id()} already in store"
        logger.error(err)
        super().__init__(err)


class ItemNotInStoreException(Exception):
    def __init__(self, item: IdentifiableProtocol):
        err = f"item {item.get_id()} not in store"
        logger.error(err)
        super().__init__(err)


class IdsNotInStoreException(Exception):
    def __init__(self, ids: Iterable[UniqueIdentifier]):
        err = f"ids {[str(x) for x in ids]} not in store"
        logger.error(err)
        super().__init__(err)


class CursorNotInStoreException(Exception):
    def __init__(self, cursor: int):
        err = f"cursor {cursor} not in store"
        logger.error(err)
        super().__init__(err)

class DataStoreProtocol(Protocol):

    def add(self,
            items: Iterable[StorableData]) -> Self:
        raise NotImplementedError()

    def update(self,
               items: Iterable[StorableData]) -> Self:
        raise NotImplementedError()

    def add_or_update(self,
                      items: Iterable[StorableData]) -> Self:
        raise NotImplementedError()

    def remove(self,
               items: Iterable[StorableData] = None,
               cursor_range: Tuple[int, int] = None,
               ids: Iterable[UniqueIdentifier] = None) -> Self:
        raise NotImplementedError()

    def get(self,
            cursor_range: Tuple[int, int] = None,
            ids: Iterable[UniqueIdentifier] = None,
            limit: int = None,
            query: Dict = None,
            id_query: PatternMatchQualifier = None) -> Dict[UniqueIdentifier, StorableData]:
        raise NotImplementedError()

    def count(self) -> int:
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def __contains__(self, item: UniqueIdentifier | StorableData):
        raise NotImplementedError()

def _find_identifyable_property(item):
    return next(x for x in SUPPORTED_IDENTIFIERS if hasattr(item, x))

def get_identifier(item: StorableData) -> UniqueIdentifier:
    if type(item) == dict and any(x in item.keys() for x in SUPPORTED_IDENTIFIERS):
        id = item[next(ii for ii in SUPPORTED_IDENTIFIERS if ii in item.keys())]
        return id
    if type(item) == str:
        try:
            val = json.loads(item)
            return get_identifier(val)
        except:
            return uuid.uuid4()
    if issubclass(type(item), IdentifiableProtocol):
        return item.get_id()
    if (prop := _find_identifyable_property(item)) is not None:
        return getattr(item, prop)
    raise ValueError(f'Un-storable item: {item}')
