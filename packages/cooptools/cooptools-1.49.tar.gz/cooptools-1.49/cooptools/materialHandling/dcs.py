from dataclasses import dataclass, field, asdict
from typing import Dict, Optional, List, Union, Tuple, Iterable, Self, Callable
from cooptools.geometry_utils import vector_utils as vec
from cooptools import coopDataclass as cdc

@dataclass(frozen=True, slots=True, kw_only=True)
class UnitOfMeasure(cdc.BaseIdentifiedDataClass):
    dimensions: vec.FloatVec3D = field(default_factory=lambda: vec.homogeneous_vector(3, 0))

DEFAULT_UOM = UnitOfMeasure(id='DEFAULT_UOM')

@dataclass(frozen=True, slots=True, kw_only=True)
class LoadCarrier(cdc.BaseIdentifiedDataClass):
    dimensions: vec.FloatVec3D = field(default_factory=lambda: vec.homogeneous_vector(3, 0))

DEFAULT_LOAD_CARRIER = LoadCarrier(id='DEFAULT_LOAD_CARRIER')

@dataclass(frozen=True, slots=True, kw_only=True)
class Load(cdc.BaseIdentifiedDataClass):
    uom: UnitOfMeasure = field(default_factory=lambda: UnitOfMeasure(id='EA'))
    weight: float = field(default=-1)
    dimensions: vec.FloatVec3D = field(default_factory=lambda: vec.homogeneous_vector(3, 0))
    load_type_categories: Iterable[str] = field(default_factory=list)
    load_carrier_type: LoadCarrier = field(default=DEFAULT_LOAD_CARRIER)

@dataclass(frozen=True, slots=True, kw_only=True)
class LocationMeta(cdc.BaseDataClass):
    dimensions: vec.FloatVec = field(default_factory=lambda: vec.homogeneous_vector(3, -1))
    boundary: vec.IterVec = None
    location_type_categories: Iterable[str] = field(default_factory=list)

    def to_jsonable_dict(self):
        ret = asdict(self)
        return ret

@dataclass(frozen=True, slots=True, kw_only=True)
class Location(cdc.BaseIdentifiedDataClass):
    meta: LocationMeta = field(default_factory=LocationMeta)
    position: vec.FloatVec3D = field(default_factory=lambda: vec.homogeneous_vector(3, -1))

LoadProvider = Load | Callable[[], Load]
LoadSelector = Callable[[Iterable[Load]], Load]
LoadListProvider = Iterable[Load] | Callable[[], Iterable[Load]]
LocationProvider = Location | Callable[[], Location]
LocationSelector = Callable[[Iterable[Location]], Location]
LocationListProvider = Iterable[Location] | Callable[[], Iterable[Location]]

if __name__ == "__main__":
    from pprint import pprint

    def test_1():
        loc1 = Location(
            position=(1, 2, 3)
        )

        load1 = Load()

        pprint(loc1)
        pprint(load1)


    test_1()