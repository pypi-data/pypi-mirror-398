import uuid
from typing import Iterable, Tuple, Dict
import logging
from pprint import pprint
from cooptools.protocols import IdentifiableProtocol, UniqueIdentifier
from cooptools.dataStore import dataStoreProtocol as dsp
from cooptools.qualifiers.qualifier import PatternMatchQualifier

logger = logging.getLogger(__name__)

class InMemoryDataStore(dsp.DataStoreProtocol):
    def __init__(self):
        """
        The store is a dictionary with the following characteristics:
            key: int -- represents the cursor value (order of entry)
            value: Tuple[UniqueIdentifier, Storable]
        """
        self._store = {}
        self._cursor = -1
        self._id_cursor_map = {}

    def _increment_cursor(self):
        self._cursor += 1
        return self._cursor

    def __contains__(self, item: UniqueIdentifier | dsp.StorableData):
        if issubclass(item, UniqueIdentifier):
            return item in self.IdKeyStore.keys()
        if issubclass(item, IdentifiableProtocol):
            return item.get_id() in self.IdKeyStore.keys()

        raise ValueError(f"Unhandled type {type(item)}")


    @property
    def Store(self) -> Dict[int, Tuple[UniqueIdentifier, dsp.StorableData]]:
        return dict(self._store)

    @property
    def IdKeyStore(self) -> Dict[UniqueIdentifier, dsp.StorableData]:
        return {
            v[0]: v[1] for k, v in self._store.items()
        }

    def _subset_of_store(self,
                         ids: Iterable[UniqueIdentifier] = None,
                         cursor_range: Tuple[int, int] | Iterable = None,
                         limit: int = None,
                         query: Dict = None) -> Dict[UniqueIdentifier, dsp.StorableData]:

        if limit is not None:
            raise ValueError(f"limit is not supported for InMemoryDataStore")

        if query is not None:
            raise ValueError(f"query is not supported for InMemoryDataStore")

        if ids is not None:
            return {k: v for k, v in self.IdKeyStore.items() if k in ids}

        if cursor_range is not None and isinstance(cursor_range, Tuple):
            return {
                v[0]: v[1] for k, v in self._store.items() if cursor_range[0] <= k <= cursor_range[1]
            }
        elif cursor_range is not None and isinstance(cursor_range, Iterable):
            return {
                v[0]: v[1] for k, v in self._store.items() if k in cursor_range
            }

        return self.IdKeyStore

    def add(self,
            items: Iterable[dsp.StorableData]) -> dsp.DataStoreProtocol:
        for item in items:
            id = dsp.get_identifier(item)
            if id in self.IdKeyStore.keys():
                raise dsp.ItemAlreadyInStoreException(item)

        new = {self._increment_cursor(): (dsp.get_identifier(x), x) for x in items}
        self._id_cursor_map = {**self._id_cursor_map, **{v[0]: k for k, v in new.items()}}
        self._store = {**self._store, **new}
        return self

    def update(self,
               items: Iterable[dsp.StorableData]) -> dsp.DataStoreProtocol:
        for item in items:
            id = dsp.get_identifier(item)
            if id not in self.IdKeyStore.keys():
                raise dsp.ItemNotInStoreException(item)

        for item in items:
            self._store[self._id_cursor_map[dsp.get_identifier(item)]] = (dsp.get_identifier(item), item)

        return self

    def add_or_update(self,
                      items: Iterable[dsp.StorableData]) -> dsp.DataStoreProtocol:
        to_add = [item for item in items if dsp.get_identifier(item) if dsp.get_identifier(item) not in self.IdKeyStore.keys()]
        to_update = [item for item in items if dsp.get_identifier(item) if dsp.get_identifier(item) in self.IdKeyStore.keys()]

        self.add(to_add)
        self.update(to_update)

        return self

    def remove(self,
               items: Iterable[dsp.StorableData] = None,
               cursor_range: Tuple[int, int] | Iterable = None,
               ids: Iterable[UniqueIdentifier] = None) -> dsp.DataStoreProtocol:

        if cursor_range is not None and isinstance(cursor_range, tuple):
            cursors_to_delete = [x for x in self._store.keys() if cursor_range[0] <= x <= cursor_range[1]]
            return self.remove(cursor_range=cursors_to_delete)
        elif cursor_range is not None and isinstance(cursor_range, Iterable):
            for cursor in cursor_range:
                id, item = self._store[cursor]
                del self._store[cursor]
                del self._id_cursor_map[id]
            return self

        if items is not None:
            return self.remove(ids=[dsp.get_identifier(x) for x in items])

        if ids is not None:
            for id in ids:
                if id not in self.IdKeyStore.keys():
                    raise dsp.IdsNotInStoreException(ids=[id])

            cursors_to_delete = [self._id_cursor_map[id] for id in ids]
            return self.remove(cursor_range=cursors_to_delete)

    def get(self,
            cursor_range: Tuple[int, int] = None,
            ids: Iterable[UniqueIdentifier] = None,
            limit: int = None,
            query: Dict = None,
            id_query: PatternMatchQualifier = None
            ) -> Dict[UniqueIdentifier, dsp.StorableData]:
        if id_query is not None:
            raise NotImplementedError(f"id_query is not implemented for InMemoryDataStore")

        return self._subset_of_store(
            ids=ids,
            cursor_range=cursor_range,
            limit=limit,
            query=query
        )

    def count(self):
        return len(self._store)

    def print(self):
        pprint(f"{self._store}")


if __name__ == "__main__":

    class Dummy:
        def __init__(self, id: uuid.UUID = None):
            self._id = id
            if self._id is None:
                self._id=uuid.uuid4()
            self.val = 'a'

        def get_id(self):
            return self._id


    def t01():
        store = InMemoryDataStore()

        store.add(
            items=[
                Dummy()
            ]
        )

        assert store.count() == 1


    def t02():
        store = InMemoryDataStore()
        ii = 10
        for i in range(ii):
            store.add(
                items=[
                    Dummy()
                ]
            )

        assert store.count() == ii


    def t03():
        store = InMemoryDataStore()
        nadd = 10
        ids = []
        for i in range(nadd):
            to_add = Dummy()
            ids.append(to_add.get_id())
            store.add(
                items=[
                    to_add
                ]
            )

        assert store.count() == nadd

        nremove = 4
        for ii in range(nremove):
            store.remove(ids=[ids[ii]])

        assert store.count() == nadd - nremove

    def t04():
        store = InMemoryDataStore()
        nadd = 10
        ids = []
        for i in range(nadd):
            to_add = Dummy()
            ids.append(to_add.get_id())
            store.add(
                items=[
                    to_add
                ]
            )

        assert store.count() == nadd

        ret = store.get(ids=[
            ids[0]
        ])

        assert ret[ids[0]].get_id() == ids[0]

    def t05():
        store = InMemoryDataStore()
        dummy = Dummy()

        store.add(items=[dummy])
        ret = store.get(ids=[dummy.get_id()])
        assert ret[dummy.get_id()].val == 'a'

        dummy2 = Dummy(id=dummy.get_id())
        dummy2.val = 'b'

        ret = store.update(items=[dummy2]).get(ids=[dummy2.get_id()])

        assert ret[dummy.get_id()].val == 'b'

    def t06():
        store = InMemoryDataStore()
        dummies = [Dummy() for ii in range(10)]

        store.add(items=dummies[:4])
        store.add_or_update(dummies)

        assert store.count() == 10


    def t_dict_add():
        store= InMemoryDataStore()
        data = [{'id': '1', "pw": 3}, {'id': '2', "pw": 3}]

        store.add(items=data)

    def t_dict_add_then_remove():
        store = InMemoryDataStore()
        nadd = 10
        ids = []
        for i in range(nadd):
            to_add = {'id': i, 'val': "whatev"}
            ids.append(dsp.get_identifier(to_add))
            store.add(
                items=[
                    to_add
                ]
            )

        assert store.count() == nadd

        nremove = 4
        for ii in range(nremove):
            store.remove(ids=[ids[ii]])

        assert store.count() == nadd - nremove


    t01()
    t02()
    t03()
    t04()
    t05()
    t06()
    t_dict_add()
    t_dict_add_then_remove()