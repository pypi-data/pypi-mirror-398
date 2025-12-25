from dataclasses import dataclass, asdict
from typing import Dict, Protocol, Tuple, Union
import datetime
from cooptools.currency import USD
from cooptools.common import verify_val
from dateutil.relativedelta import relativedelta
from cooptools.finance import utils as futil
import cooptools.date_utils as du

class ProjectionProtocol(Protocol):
    def projection(self,
                   start_date: datetime.date,
                   end_date: datetime.date,
                   **kwargs) -> Dict:
        pass

@dataclass(frozen=True, slots=True)
class InflationProjection(ProjectionProtocol):
    start_date: datetime.date
    end_date: datetime.date
    annual_inflation: float
    target: USD
    safety_factor: float = None

    @property
    def Days(self) -> int:
        return du.increment_between(
            d1=self.start_date,
            d2=self.end_date,
            increment_type=du.DateIncrementType.DAY
        )

    @property
    def InflationAdjustedTarget(self) -> USD:
        return futil.inflated_value(value=self.target, days=self.Days, annual_inflation=self.annual_inflation)

    @property
    def InflationAjdustedTargetWithSafety(self) -> USD:
        return futil.inflated_value(value=self.target * (1 + self.safety_factor), days=self.Days, annual_inflation=self.annual_inflation)

    def my_dict_v1(self):
        return {**{k: float(v) if type(v) in [USD] else v
            for k, v in asdict(self).items()},
         **{
             'days': self.Days,
             'inflation_adjusted_target': float(self.InflationAdjustedTarget),
             'inflation_adjusted_target_with_safety': float(self.InflationAjdustedTargetWithSafety),
             'target': float(self.target),
         }
         }

@dataclass(frozen=True, slots=True)
class DiscountedProjection(ProjectionProtocol):
    start_date: datetime.date
    end_date: datetime.date
    annual_discount: float

    @property
    def Days(self) -> int:
        return du.increment_between(
            d1=self.start_date,
            d2=self.end_date,
            increment_type=du.DateIncrementType.DAY
        )

    @property
    def InflationAdjustedTarget(self) -> USD:
        return futil.inflated_value(value=self.target, days=self.Days, annual_inflation=self.annual_inflation)

    @property
    def InflationAjdustedTargetWithSafety(self) -> USD:
        return futil.inflated_value(value=self.target * (1 + self.safety_factor), days=self.Days, annual_inflation=self.annual_inflation)

    def my_dict_v1(self):
        return {**{k: float(v) if type(v) in [USD] else v
            for k, v in asdict(self).items()},
         **{
             'days': self.Days,
             'inflation_adjusted_target': float(self.InflationAdjustedTarget),
             'inflation_adjusted_target_with_safety': float(self.InflationAjdustedTargetWithSafety),
             'target': float(self.target),
         }
         }


@dataclass(frozen=True, slots=True)
class FutureValueProjection(ProjectionProtocol):
    start_date: datetime.date
    end_date: datetime.date
    present_value: USD
    monthly_contributions: USD
    annual_growth_rate: float

    @property
    def Months(self):
        return du.increment_between(
            d1=self.start_date,
            d2=self.end_date,
            increment_type=du.DateIncrementType.MONTH
        )


    @property
    def FutureValueOfPresentValue(self):
        return futil.future_value(
            per_period_rate=futil.monthly_equivalent_rate(self.annual_growth_rate),
            periods=self.Months,
            present_value=self.present_value,
        )

    @property
    def FutureValueOfContributions(self):
        return futil.future_value(
            per_period_rate=futil.monthly_equivalent_rate(self.annual_growth_rate),
            periods=self.Months,
            per_period_contribution=self.monthly_contributions
        )

    @property
    def GainOfPresentValue(self):
        return self.FutureValueOfPresentValue - self.present_value

    @property
    def TotalMonthlyContributions(self):
        return self.Months * self.monthly_contributions

    @property
    def TotalContributions(self):
        return self.TotalMonthlyContributions + self.present_value

    @property
    def GainOfMonthlyContributions(self):
        return self.FutureValueOfContributions - self.TotalMonthlyContributions

    @property
    def RoIOfMonthlyContributions(self):
        if self.TotalMonthlyContributions == USD.zero():
            return None

        return self.GainOfMonthlyContributions / self.TotalMonthlyContributions

    @property
    def RoIOfPresentValue(self):
        if self.present_value == USD.zero():
            return None

        return self.GainOfPresentValue / self.present_value

    @property
    def FutureValue(self) -> USD:
        return futil.future_value(
                per_period_rate=futil.monthly_equivalent_rate(self.annual_growth_rate),
                periods=self.Months,
                present_value=self.present_value,
                per_period_contribution=self.monthly_contributions
            )

    @property
    def Gain(self) -> USD:
        return self.GainOfPresentValue + self.GainOfMonthlyContributions

    @property
    def ROI(self) -> USD:
        if (self.present_value + self.TotalContributions) == USD.zero():
            return None

        return self.Gain / (self.present_value + self.TotalContributions)

    def my_dict_v1(self):
        return {**{k: float(v) if type(v) in [USD] else v
                   for k, v in asdict(self).items()},
               **{
                    'gain': float(self.Gain),
                    'months': self.Months,
                    'total_contributions': float(self.TotalContributions),
                    'total_monthly_contributions': float(self.TotalMonthlyContributions),
                    'gain_of_present_value': float(self.GainOfPresentValue),
                    'gain_of_contributions': float(self.GainOfMonthlyContributions),
                    'future_value_of_contributions': float(self.FutureValueOfContributions),
                    'future_value_of_present_value': float(self.FutureValueOfPresentValue),
                    'future_value': float(self.FutureValue),
                    'roi_of_present_value': self.RoIOfPresentValue,
                    'roi_of_contributions': self.RoIOfMonthlyContributions,
                    'roi': self.ROI,
                    'present_value': float(self.present_value),
                    'monthly_contributions': float(self.monthly_contributions)

                    }
                }

def projection(
        start_year: int,
        start_mo: int,
        projection_evaluator: ProjectionProtocol,
        projected_months: int = None,
        **kwargs
) -> Dict[datetime.date, ProjectionProtocol]:
    if projected_months is None:
        projected_months = 100

    verify_val(start_mo, gte=1, lte=12)

    start_date = datetime.date(year=start_year, month=start_mo, day=1)
    epoch_date = start_date

    ret = {}
    for ii in range(projected_months):
        ret[epoch_date] = projection_evaluator.projection(start_date=start_date,
                                                           end_date=epoch_date,
                                                           **kwargs)
        epoch_date = epoch_date + relativedelta(months=1)

    return ret

def inflation_projections(
        target: USD,
        safety_factor: float,
        start_year:int,
        start_mo: int,
        annual_inflation: float,
        projected_months: int = None
) -> Dict[datetime.date, InflationProjection]:
    if projected_months is None:
        projected_months = 100

    ret = {}
    start_date = datetime.datetime(year=start_year, month=start_mo, day=1)
    for epoch_date in du.datetime_generator(
        start_date_time=start_date,
        end_date_time=start_date + relativedelta(months=projected_months),
        increment_type=du.DateIncrementType.MONTH
    ):
        ret[epoch_date] = InflationProjection(
            start_date=start_date,
            end_date=epoch_date,
            annual_inflation=annual_inflation,
            target=target,
            safety_factor=safety_factor
        )

    return ret

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

def future_value_projections(
        present_value: USD,
        monthly_contributions: USD,
        start_year: int,
        start_mo: int,
        growth_rate: Union[float, Dict[float, Tuple[du.DateIncrementType, int]]],
        projected_months: int = None,
) -> Dict[datetime.date, FutureValueProjection]:
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

        ret[epoch_date] = FutureValueProjection(
            start_date=start_date,
            end_date=epoch_date,
            present_value=present_value,
            monthly_contributions=monthly_contributions,
            annual_growth_rate=_rate
        )

    return ret


def fund_projection(
        present_value: USD,
        monthly_contributions: USD,
        start_year: int,
        start_mo: int,
        annual_rate: float,
        target: USD,
        safety_factor: float,
        annual_inflation: float,
        projected_months: int = None,
        as_dict: bool = False,
        as_df: bool = False,
):
    target_projections = inflation_projections(
        target=target,
        safety_factor=safety_factor,
        start_year=start_year,
        start_mo=start_mo,
        annual_inflation=annual_inflation,
        projected_months=projected_months
    )

    fv_proj = future_value_projections(
        present_value=present_value,
        monthly_contributions=monthly_contributions,
        start_year=start_year,
        start_mo=start_mo,
        growth_rate=annual_rate,
        projected_months=projected_months
    )

    merged = {
        k: (v, fv_proj[k])
    for k, v in target_projections.items()}

    if as_dict or as_df:
        merged = {
            k: {**v[0].my_dict_v1(),
                **v[1].my_dict_v1()}
            for k, v in merged.items()
        }

    if as_df:
        merged = pd.DataFrame(data=merged.values())

    return merged





if __name__ == "__main__":
    from pprint import pprint
    import pandas as pd
    from cooptools.pandasHelpers import pretty_print_dataframe
    from cooptools.plotting import plot_series, plot_datetime
    import matplotlib.pyplot as plt

    start_year = 2018
    start_mo = 5
    maar = 0.075

    def test_1():
        inf_proj = inflation_projections(
            target=USD.from_val(40000),
            safety_factor=0.1,
            start_year=start_year,
            start_mo=start_mo,
            annual_inflation=0.015,
        )

        fv_proj = future_value_projections(
            present_value=USD.from_val(1000),
            monthly_contributions=USD.from_val(150),
            start_year=start_year,
            start_mo=start_mo,
            growth_rate=maar,
        )
        df = pd.DataFrame(data=[x.my_dict_v1() for x in inf_proj.values()])
        pretty_print_dataframe(df)

        df = pd.DataFrame(data=[x.my_dict_v1() for x in fv_proj.values()])
        pretty_print_dataframe(df)

        ax = df[['end_date', 'gain', 'roi', 'total_contributions', 'future_value']] \
            .plot(x='end_date',
                  y=['gain', 'total_contributions', 'future_value'])
        df[['end_date', 'gain', 'roi', 'total_contributions', 'future_value']] \
            .plot(x='end_date',
                  y=['roi'],
                  secondary_y=True,
                  ax=ax)
        plt.show()

    def test_2():
        df = fund_projection(
            present_value=USD.from_val(1000),
            monthly_contributions=USD.from_val(350),
            start_year=start_year,
            start_mo=start_mo,
            annual_rate=maar,
            target=USD.from_val(40000),
            safety_factor=0.1,
            annual_inflation=0.015,
            as_df=True
        )
        pretty_print_dataframe(df)

        graphable = df[[x for x in df.columns if x not in ['start_date',
                                                           'safety_factor',
                                                           'days',
                                                           'months',
                                                           'annual_inflation',
                                                           'present_value',
                                                           'annual_rate',
                                                           'monthly_contributions',
                                                           'future_value_of_present_value',
                                                           'future_value_of_contributions',
                                                           'roi_of_contributions',
                                                           'roi_of_present_value',
                                                           'roi',
                                                           'total_monthly_contributions',
                                                           'gain_of_present_value',
                                                           'gain_of_contributions']]]
        fig, ax = plt.subplots(figsize=(10, 5))

        draw_args = {
            'target': ('dotted', 0.5),
            'inflation_adjusted_target': ('solid', 1),
            'inflation_adjusted_target_with_safety': ('dotted', 0.5),
            'gain': ('dotted', 0.5),
            'total_contributions': ('dotted', 0.5),
            'future_value': ('solid', 1)
        }

        x_axis = 'end_date'
        for x in graphable.columns:
            if x == x_axis:
                continue

            graphable.plot(
                ax=ax,
                x=x_axis,
                y=x,
                linestyle=draw_args[x][0],
                linewidth=draw_args[x][1]
            )

        plt.show()



    test_2()
