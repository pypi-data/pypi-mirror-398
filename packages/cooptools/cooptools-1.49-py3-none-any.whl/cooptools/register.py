from typing import Dict, Iterable, Generic, TypeVar, List

T = TypeVar("T")

class Register(Generic[T]):
    def __init__(self, to_register: Iterable[T] = None, ids: Iterable[str] = None):
        self._registry: Dict[str, T] = {}

        if to_register is not None:
            self.register(to_register, ids)

    @property
    def Registry(self) -> Dict[str, T]:
        return self._registry

    def register(self, to_register: Iterable[T], ids: Iterable[str]):
        self._registry = {**self._registry, **{ids[ii]: x for ii, x in enumerate(to_register)}}
        return self

    def unregister(self, ids: Iterable[str]):
        self._registry = {k: v for k, v in self._registry.items() if k not in ids}
        return self

    def get_by_id(self, ids: Iterable[str]) -> List[T]:
        return [self._registry[x] for x in ids]