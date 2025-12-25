from dataclasses import dataclass, asdict
from typing import Dict, Protocol, Tuple, Union
import datetime
from cooptools.currency import USD
from cooptools.common import verify_val
from dateutil.relativedelta import relativedelta
from cooptools.finance import utils as futil
import cooptools.date_utils as du
from cooptools.finance import growth_projections as gps

def _resolve_growth_rate(growth_rate: Union[float, Dict[float, Tuple[du.DateIncrementType, int]]],
                         start_date: datetime.datetime,
                         epoch_date: datetime.datetime):
    _rate = growth_rate
    if type(growth_rate) != float:
        for rate, period in growth_rate.items():
            increment_type, periods = period
            _rate = rate

            end_of_growth_phase = du.datetime_add(start_date=start_date, increment_type=increment_type, increments=periods)
            if end_of_growth_phase > epoch_date:
                break
    return _rate



class FutureValueProjector:
    def __init__(self):
        pass

    def project(
            present_value: USD,
            monthly_contributions: USD,
            start_year: int,
            start_mo: int,
            growth_rate: Union[float, Dict[float, Tuple[du.DateIncrementType, int]]],
            projected_months: int = None,
    ) -> Dict[datetime.date, gps.FutureValueProjection]:
        if projected_months is None:
            projected_months = 100

        ret = {}
        start_date = datetime.datetime(year=start_year, month=start_mo, day=1)
        for epoch_date in du.datetime_generator(
                start_date_time=start_date,
                end_date_time=start_date + relativedelta(months=projected_months),
                increment_type=du.DateIncrementType.MONTH
        ):
            _rate = _resolve_growth_rate(growth_rate=growth_rate,
                                         start_date=start_date,
                                         epoch_date=epoch_date)

            ret[epoch_date] = gps.FutureValueProjection(
                start_date=start_date,
                end_date=epoch_date,
                present_value=present_value,
                monthly_contributions=monthly_contributions,
                annual_growth_rate=_rate
            )

        return ret