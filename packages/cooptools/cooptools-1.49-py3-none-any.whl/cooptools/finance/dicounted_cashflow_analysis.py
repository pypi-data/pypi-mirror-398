import datetime
from cooptools.currency import USD
import cooptools.finance.growth_projections as gp
import cooptools.date_utils as du

def discounted_cashflows():

    cashflows = gp.future_value_projections(
        present_value=USD.from_val(1000),
        monthly_contributions=USD.from_val(250),
        start_year=2000,
        start_mo=10,
        growth_rate={0.1: (du.DateIncrementType.YEAR, 3),
                     0.04: (du.DateIncrementType.YEAR, 3)},
        projected_months=12*10
    )

    return cashflows


if __name__ == "__main__":
    from pprint import pprint

    # MONTHLY = USD.from_val(250)
    # MAAR_ANNUAL = 0.10
    #
    # cashflows = {
    #     datetime.datetime(year=2023, month=ii+1, day=1): MONTHLY for ii in range(12)
    # }
    #
    # pprint(cashflows)

    def test_1():
        cashflows = discounted_cashflows()
        pprint({k: (v.annual_growth_rate, v.FutureValue) for k, v in cashflows.items()})

    test_1()