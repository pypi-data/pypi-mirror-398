import datetime
import math
import pprint
from dataclasses import dataclass
from cooptools.currency import USD
from typing import Dict, Tuple
import cooptools.date_utils as du

@dataclass(frozen=True, slots=True)
class Cashflow:
    date: datetime.date
    amount: USD

def aggregate_inflation(
        annual_inflation: float,
        days: int
) -> float:
    return (1 + annual_inflation) ** (days / 365)

def inflated_value(
        value: USD,
        annual_inflation: float,
        days: int
) -> USD:
    return aggregate_inflation(annual_inflation, days) * value

def monthly_equivalent_rate(annual_rate: float):
    return (1 + annual_rate) ** (1 / 12) - 1

def future_value_factor(
        per_period_rate: float,
        periods: float
):
    return (1+per_period_rate) ** periods

def present_value_factor(
        per_period_rate: float,
        periods: float
):
    return 1 / future_value_factor(per_period_rate=per_period_rate, periods=periods)


def future_value_of_annuity(
        per_period_rate: float,
        periods: float,
        per_period_contribution: USD=None
):
    if per_period_contribution is None:
        per_period_contribution = USD.zero()

    fv_factor = future_value_factor(per_period_rate=per_period_rate, periods=periods)

    if math.isclose((fv_factor - 1), per_period_rate):
        return per_period_contribution

    return per_period_contribution * ((fv_factor - 1) / per_period_rate)

def future_value_of_present_value(
        per_period_rate: float,
        periods: float,
        present_value: USD = None,
):
    if present_value is None:
        present_value = USD.zero()
    return future_value_factor(per_period_rate=per_period_rate,periods=periods) * present_value

def future_value_of_cashflow(cashflow: Cashflow,
                             future_date: datetime.date,
                             per_period_rate: float,
                             ):

    #TODO: Calculate periods between cashflow date and future date
    periods = ... (future_date - cashflow.date)

    return future_value_of_present_value(
        per_period_rate=per_period_rate,
        periods=periods,
        present_value=cashflow.amount
    )

def future_value(
        per_period_rate: float,
        periods: float,
        present_value: USD = None,
        per_period_contribution: USD = None,
):
    annuity = future_value_of_annuity(
        per_period_contribution=per_period_contribution,
        per_period_rate=per_period_rate,
        periods=periods
    )

    fv = future_value_of_present_value(
        per_period_rate=per_period_rate,
        periods=periods,
        present_value=present_value
    )

    return fv + annuity



def present_value_of_future_value(
        per_period_rate: float,
        periods: float,
        future_value: USD = None,
) -> USD:
    if future_value is None:
        future_value = USD.zero()

    present_value = future_value * present_value_factor(per_period_rate=per_period_rate, periods=periods)

    return present_value

def present_value_of_annuity(
        per_period_rate: float,
        periods: float,
        per_period_contribution: USD=None
):
    if per_period_contribution is None:
        per_period_contribution = USD.zero()

    pv_factor = present_value_factor(per_period_rate=per_period_rate, periods=periods)

    pv_annuity = (per_period_contribution / per_period_rate) * (1 - pv_factor)

    return pv_annuity

def present_value(
        per_period_rate: float,
        periods: float,
        future_value: USD = None,
        per_period_contribution: USD = None,
):
    pv_annuity = present_value_of_annuity(
        per_period_contribution=per_period_contribution,
        per_period_rate=per_period_rate,
        periods=periods
    )

    pv = present_value_of_future_value(
        per_period_rate=per_period_rate,
        periods=periods,
        future_value=future_value
    )

    return pv + pv_annuity


def adjust_cashflows(
        per_period_rate: float,
        cashflows: Dict[datetime.datetime | datetime.date, USD],
        period_type: du.DateIncrementType,
        adjustment_date: datetime.datetime | datetime.date = None
) -> Dict[datetime.datetime | datetime.date, Tuple[USD, USD]]:
    if adjustment_date is None:
        adjustment_date = datetime.datetime.today()

    ret = {}
    for date, cashflow in cashflows.items():
        periods_between = du.increment_between(
            d1=adjustment_date,
            d2=date,
            increment_type=period_type
        )

        if periods_between > 0:
            adjusted_cashflow = present_value(
                per_period_rate=per_period_rate,
                periods=periods_between,
                future_value=cashflow
            )
        else:
            adjusted_cashflow = future_value(
                per_period_rate=per_period_rate,
                periods=-periods_between,
                present_value=cashflow
            )
        ret[date] = (cashflow, adjusted_cashflow)
    return ret


if __name__ == "__main__":
    def test_1():
        print(aggregate_inflation(0.015, 450))

        print(future_value(
            per_period_rate=0.06/12,
            periods=5 * 12,
            present_value=USD.from_val(1000),
            per_period_contribution=USD.from_val(250)
        ))

    def test_2():
        MONTHLY = USD.from_val(250)
        MAAR_ANNUAL = 0.10

        cashflows = {
            datetime.datetime(year=2023, month=ii + 1, day=1): MONTHLY for ii in range(12)
        }
        cashflows.update(
            {
                datetime.datetime(year=2024, month=ii + 1, day=1): MONTHLY for ii in range(12)
        }
        )

        adjusted_cfs = adjust_cashflows(
            per_period_rate=MAAR_ANNUAL,
            cashflows=cashflows,
            period_type=du.DateIncrementType.YEAR,
        )

        pprint.pprint(adjusted_cfs)
    test_2()