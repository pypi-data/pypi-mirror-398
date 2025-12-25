from cooptools.materialHandling import dcs
from cooptools.cli.CliAtomicUserInteraction import CliAtomicUserInteraction as cli

def request_uom() -> dcs.UnitOfMeasure:

    return dcs.UnitOfMeasure(
        id=cli.request_string("UoM Id: "),
        dimensions=cli.request_float_tuple(
                prompt=f"UoM Dimensions (m): ",
                min=0,
                len_limit=3
            ),
    )

def request_load() -> dcs.Load:
    return dcs.Load(
        id=cli.request_string("Load Id: "),
        uom=request_uom(),
        weight=cli.request_float(f"Weight (lbs): "),
        dimensions=cli.request_float_tuple(
                prompt=f"Load Dimensions (m): ",
                min=0,
                len_limit=3
            ),
        load_type_categories=cli.request_list("Load Type Categories: "),
        load_carrier_type=cli.request_string("Load Carrier Type: ")
    )

