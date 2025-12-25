from dataclasses import dataclass, field
from typing import Iterable, Dict
from cooptools.qualifiers import qualifier as qual
from cooptools.protocols import UniqueIdentifier
from cooptools.materialHandling import dcs as mh_dcs

@dataclass(frozen=True, slots=True)
class LocationQualifier(qual.QualifierProtocol):
    location: mh_dcs.Location = None
    id_qualifier: qual.PatternMatchQualifier = field(default_factory=qual.PatternMatchQualifier)
    dim_qualifer: qual.DimensionQualifier = field(default_factory=qual.DimensionQualifier)
    location_type_white_black_qualifier: qual.WhiteBlackManyListQualifier = field(default_factory=qual.WhiteBlackManyListQualifier)

    def qualify(self, values: Iterable[mh_dcs.Location]) -> Dict[mh_dcs.Location, qual.QualifierResponse]:
        if self.location is not None:
            loc_quals = {x.id: qual.QualifierResponse(x==self.location, failure_reasons=[f"{x}!={self.location}"] if x!=self.location else []) for x in values}
        else:
            loc_quals = {x.id: qual.QualifierResponse(True) for x in values}


        id_quals = self.id_qualifier.qualify([x.id for x in values])
        dim_quals = self.dim_qualifer.qualify([x.meta.dimensions for x in values])
        location_type_white_black_quals = self.location_type_white_black_qualifier.qualify(
            [x.meta.location_type_categories for x in values]
        )

        return {
            x.id: qual.QualifierResponse(
                result=all([
                    loc_quals[x.id],
                    id_quals[x.id],
                    dim_quals[idx],
                    location_type_white_black_quals[idx]]
                ),
                failure_reasons=id_quals[x.id].failure_reasons +
                                dim_quals[idx].failure_reasons +
                                location_type_white_black_quals[idx].failure_reasons +
                                loc_quals[x.id].failure_reasons


            )
            for idx, x in enumerate(values)
        }



@dataclass(frozen=True, slots=True)
class LoadQualifier:
    load: mh_dcs.Load = None
    id_qualifier: qual.PatternMatchQualifier = field(default_factory=qual.PatternMatchQualifier)
    dim_qualifer: qual.DimensionQualifier = field(default_factory=qual.DimensionQualifier)
    load_type_white_black_qualifier: qual.WhiteBlackManyListQualifier = field(default_factory=qual.WhiteBlackManyListQualifier)

    def qualify(self, values: Iterable[mh_dcs.Load]) -> Dict[UniqueIdentifier, qual.QualifierResponse]:
        if self.load is not None:
            load_quals = {x.id: qual.QualifierResponse(x==self.load, failure_reasons=[f"{x}!={self.load}"] if x!=self.load else []) for x in values}
        else:
            load_quals = {x.id: qual.QualifierResponse(True) for x in values}
        id_quals = self.id_qualifier.qualify([x.id for x in values])
        dim_quals = self.dim_qualifer.qualify([x.dimensions for x in values])
        load_type_white_black_quals = self.load_type_white_black_qualifier.qualify(
            [x.load_type_categories for x in values]
        )

        return {
            x.id: qual.QualifierResponse(
                result=all([
                    load_quals[x.id],
                    id_quals[x.id],
                    dim_quals[idx],
                    load_type_white_black_quals[idx]]
                ),
                failure_reasons=id_quals[x.id].failure_reasons +
                                dim_quals[idx].failure_reasons +
                                load_type_white_black_quals[idx].failure_reasons +
                                load_quals[x.id].failure_reasons

            )
            for idx, x in enumerate(values)
        }





if __name__ == "__main__":
    from cooptools.materialHandling import Location, LocationMeta
    from pprint import pprint

    meta1 = LocationMeta(
        dimensions=(1, 1, 1),
        location_type_categories=['T1']
    )
    meta2 = LocationMeta(
        dimensions=(100, 100, 100),
        location_type_categories=['T5']
    )
    meta3 = LocationMeta(
        dimensions=(100, 100, 100),
        location_type_categories=['T5']
    )

    def test_001():
        locations = [
            l1 := Location(id='A1', meta=meta1),
            l2 := Location(id='A2', meta=meta2),
            l3 := Location(id='B1', meta=meta1),
            l4 := Location(id='B2', meta=meta1)
        ]

        pprint(qual.IdDimQualifier(
            id_pattern=qual.PatternMatchQualifier(regex_any=[r'.*2', 'A']),
            dim_qualifer=qual.DimensionQualifier(
                max_dims=(10, 10, 10)
            )
        ).qualify(
            [(x.id, x.meta.dimensions) for x in locations]
        ))

    def test_002():
        locations = [
            l1 := Location(id='A1', meta=meta1),
            l2 := Location(id='A2', meta=meta2),
            l3 := Location(id='B1', meta=meta1),
            l4 := Location(id='B2', meta=meta3)
        ]

        lq = LocationQualifier(
            id_qualifier=qual.PatternMatchQualifier(regex_any=[r'.*2', 'A']),
            dim_qualifer=qual.DimensionQualifier(
                max_dims=(10, 10, 10)
            ),
            location_type_white_black_qualifier=qual.WhiteBlackManyListQualifier(
                white_black_list_qualifier=qual.WhiteBlackListQualifier(
                    white_list=['T1', 'T2', 'T3'],
                    black_list=['T5']
                ),
                any_in_white=True,
                none_in_black=True

            )
        )

        pprint(lq.qualify(locations))

    test_001()
    test_002()
