import matplotlib.pyplot as plt
import pandas as pd
from cooptools import typeProviders as tp
from cooptools import pandasHelpers as ph
import datetime
from cooptools.coopEnum import CoopEnum, auto
import cooptools.date_utils as du
import numpy as np
from cooptools import plotting as cplt
from dataclasses import dataclass
from cooptools.colors import Color
from typing import Dict


class PivotProfileType(CoopEnum):
    DATESTAMP_ACCOUNT__CATEGORY = auto()
    ACCOUNT_CATEGORY__DATESTAMP = auto()
    DATESTAMP__CATEGORY = auto()
    CATEGORY__DATESTAMP = auto()
    DATESTAMP__ACCOUNT = auto()
    DATESTAMP = auto()
    ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP = auto()
    DATESTAMP__SUBACCOUNT = auto()
    SUBACCOUNT_CATEGORY__DATESTAMP = auto()
    DATESTAMP_SUBACCOUNT__CATEGORY = auto()


DATE_STAMP_COL = 'date_stamp'
CATEGORY_COL = 'category'
ACCOUNT_COL = 'account'
AMOUNT_COL = 'amount'
SUBACCOUNT_COL = 'subaccount'
INCOME_COL = 'income'
EXPENSE_COL = 'expense'
ASSET_COL = 'assets'
LIAB_COL = 'liabilities'
NE_COL = 'net_equity'
NE_INTERP_COL = 'net_equity_interpolated'
AVAIL_CAP_COL = 'available_capital'
FI_MONTH_CASH_COL = 'fi_monthly_cashflow'
PROJECTED_FI_MONTH_CASH_COL = 'projected_fi_cashflow'
AVG_6MO_EXP_COL = '6mo_avg_expenses'
AVG_6MO_INC_COL = '6mo_avg_income'
AVG_6MO_MARGIN_COL = '6mo_avg_margin'
AVG_INC_COL = 'avg_income'
AVG_EXP_COL = 'avg_expenses'
FI_TARGET_COL = 'fi_target'
DOLLAR_FMT = '{:,.2f}'
DATE_CALC_STR = 'date_str'
LIAB_INTERP = 'liabilities_interpoloated'
ASSET_INTERP = 'assets_interpoloated'
DELTA_LIAB = 'delta_liabilities'
DELTA_ASSET = 'delta_assets'
DELTA_EQUITY = 'delta_equity'
CURRENT_RATIO = 'current_ratio'
QUICK_RATIO = 'quick_ratio'
VAL_ABOVE_LIAB = 'value_above_liabilities'
PERC_GAIN = 'perc_gain'
EFF_APY = 'effective_apy'
PROJECTED_NE_AT_MARR = 'projected_net_equity_at_marr'

def _groupers(grouped_history_type: PivotProfileType,
              date_group_frequency: str = 'ME',
              date_stamp_col_name: str = None,
              category_col_name: str = None,
              account_col_name: str = None,
              subaccount_col_name: str = None):
    if date_stamp_col_name is None:
        date_stamp_col_name = DATE_STAMP_COL
    if category_col_name is None:
        category_col_name = CATEGORY_COL
    if account_col_name is None:
        account_col_name = ACCOUNT_COL
    if subaccount_col_name is None:
        subaccount_col_name = SUBACCOUNT_COL
    grouper_lst = []

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.DATESTAMP__CATEGORY,
                                PivotProfileType.DATESTAMP__ACCOUNT,
                                PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP__SUBACCOUNT,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP]:
        grouper_lst.append(pd.Grouper(key=date_stamp_col_name, freq=date_group_frequency))

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.DATESTAMP__CATEGORY,
                                PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.CATEGORY__DATESTAMP,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP
                                ]:
        grouper_lst.append(category_col_name)

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP__ACCOUNT,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP]:
        grouper_lst.append(account_col_name)

    if grouped_history_type in [PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP__SUBACCOUNT,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP
                                ]:
        grouper_lst.append(subaccount_col_name)

    if len(grouper_lst) == 0:
        raise ValueError(f"Groupers have not been correctly evaluated")

    return grouper_lst


def _pivot_indexes(grouped_history_type: PivotProfileType,
                   date_stamp_col_name: str = None,
                   category_col_name: str = None,
                   account_col_name: str = None,
                   subaccount_col_name: str = None):
    if date_stamp_col_name is None:
        date_stamp_col_name = DATE_STAMP_COL
    if category_col_name is None:
        category_col_name = CATEGORY_COL
    if account_col_name is None:
        account_col_name = ACCOUNT_COL
    if subaccount_col_name is None:
        subaccount_col_name = SUBACCOUNT_COL
    pivot_index = []

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.DATESTAMP__CATEGORY,
                                PivotProfileType.DATESTAMP__ACCOUNT,
                                PivotProfileType.DATESTAMP,
                                PivotProfileType.DATESTAMP__SUBACCOUNT,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY
                                ]:
        pivot_index.append(date_stamp_col_name)

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP]:
        pivot_index.append(account_col_name)

    if grouped_history_type in [PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY
                                ]:
        pivot_index.append(subaccount_col_name)

    if grouped_history_type in [PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.CATEGORY__DATESTAMP,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP,
                                ]:
        pivot_index.append(category_col_name)

    return pivot_index


def _pivot_columns(grouped_history_type: PivotProfileType,
                   date_stamp_col_name: str = None,
                   category_col_name: str = None,
                   account_col_name: str = None,
                   subaccount_col_name: str = None
                   ):
    if date_stamp_col_name is None:
        date_stamp_col_name = DATE_STAMP_COL
    if category_col_name is None:
        category_col_name = CATEGORY_COL
    if account_col_name is None:
        account_col_name = ACCOUNT_COL
    if subaccount_col_name is None:
        subaccount_col_name = SUBACCOUNT_COL

    pivot_columns = []

    if grouped_history_type in [PivotProfileType.DATESTAMP_ACCOUNT__CATEGORY,
                                PivotProfileType.DATESTAMP__CATEGORY,
                                PivotProfileType.DATESTAMP_SUBACCOUNT__CATEGORY
                                ]:
        pivot_columns.append(category_col_name)

    if grouped_history_type in [PivotProfileType.ACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.CATEGORY__DATESTAMP,
                                PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
                                PivotProfileType.SUBACCOUNT_CATEGORY__DATESTAMP,
                                ]:
        pivot_columns.append(date_stamp_col_name)

    if grouped_history_type in [PivotProfileType.DATESTAMP__ACCOUNT,
                                ]:
        pivot_columns.append(account_col_name)

    if grouped_history_type in [
        PivotProfileType.DATESTAMP__SUBACCOUNT,
    ]:
        pivot_columns.append(subaccount_col_name)

    return pivot_columns


def amount_pivot(
        history_df_provider: tp.DataFrameProvider,
        start_date: datetime.date = None,
        end_date: datetime.date = None,
        grouped_history_type: PivotProfileType = None,
        date_stamp_col_name: str = DATE_STAMP_COL,
        category_col_name: str = CATEGORY_COL,
        account_col_name: str = ACCOUNT_COL,
        subaccount_col_name: str = SUBACCOUNT_COL,
        amount_col_name: str = AMOUNT_COL,
        invert_amounts: bool = False,
        sig_dig: int = 3
):
    df = tp.resolve(history_df_provider)
    df = ph.clean_a_dataframe(
        df=df,
        column_type_definition={
            date_stamp_col_name: datetime.date,
            category_col_name: str,
            account_col_name: str,
            subaccount_col_name: str,
            amount_col_name: float
        }
    )

    if invert_amounts:
        df[amount_col_name] = -df[amount_col_name]

    grouper_lst = _groupers(grouped_history_type,
                            account_col_name=account_col_name,
                            category_col_name=category_col_name,
                            date_stamp_col_name=date_stamp_col_name,
                            subaccount_col_name=subaccount_col_name)
    pivot_index = _pivot_indexes(grouped_history_type,
                                 account_col_name=account_col_name,
                                 category_col_name=category_col_name,
                                 date_stamp_col_name=date_stamp_col_name,
                                 subaccount_col_name=subaccount_col_name)
    pivot_columns = _pivot_columns(grouped_history_type,
                                   account_col_name=account_col_name,
                                   category_col_name=category_col_name,
                                   date_stamp_col_name=date_stamp_col_name,
                                   subaccount_col_name=subaccount_col_name)

    agg_val = amount_col_name
    pivot_index_amounts = df[pivot_index + pivot_columns + [agg_val]]
    agg_amounts = pivot_index_amounts.groupby(grouper_lst).sum()

    # Pivot
    if not agg_amounts.empty:
        piv = pd.pivot_table(agg_amounts,
                             values=agg_val,
                             index=pivot_index,
                             columns=pivot_columns,
                             aggfunc='sum').fillna(0).round(sig_dig)
    else:
        piv = pd.DataFrame()

    # piv = piv.sort_values(by= axis=1, ascending=True)

    # pad missing months
    if date_stamp_col_name in pivot_columns:
        if end_date is None:
            end_date = du.date_tryParse(pivot_index_amounts[date_stamp_col_name].max())

        if start_date is None:
            start_date = du.date_tryParse(pivot_index_amounts[date_stamp_col_name].min())

        for mo in du.month_range(start_date, end_date):
            col = mo.strftime("%Y-%m")
            if col not in piv.columns:
                piv[col] = np.nan

        piv.columns = [x.strftime("%Y-%m") for x in piv.columns]
    # Re-order the columns based on their sum
    # piv = piv.reindex(piv.sum().sort_values(ascending=False).index, axis=1)
    # piv['row_sum'] = piv.sum(axis=1)
    # Sort by the row sums
    # piv = piv.sort_values(by='amount', ascending=False)
    # piv.drop('row_sum', axis=1, inplace=True)

    # Format date_stamp as year-mo
    # piv = piv.reset_index()
    if date_stamp_col_name in pivot_index:
        piv.index = piv.index.strftime('%Y-%m')

    return piv


def pivot_recorded_values(df: pd.DataFrame):
    piv = df.pivot_table(index=['type', 'horizon', 'category'], columns='date', values='value')
    cols = list(piv.columns)
    cols.reverse()
    piv = piv[cols]
    piv = piv.fillna('-')
    piv = piv.replace({0: '-'})

    return piv


def grouped_data(df: pd.DataFrame,
                 echo: bool = False):
    gpd = df.groupby(
        ['date', 'type', 'horizon']
    )['value'].sum().reset_index()

    if echo:
        ph.pretty_print_dataframe(gpd)
    return gpd


def pivot(df: pd.DataFrame,
          echo: bool = False):
    piv = df.pivot_table(index=['type', 'category', 'horizon'], columns=['date'], values='value', aggfunc='sum')
    piv.columns = [x.strftime("%Y-%m") for x in piv.columns]

    if echo:
        ph.pretty_print_dataframe(piv)
    piv = piv.reset_index()
    return piv


def _project_at_rate(value, rate, periods):
    return value * (1 + rate) ** periods


def balance_sheet_summary(df: pd.DataFrame,
                          asset_col_name: str = ASSET_COL,
                          liab_col_name: str = LIAB_COL,
                          echo: bool = False,
                          marr: float = 0.05):
    GRP_VAL = 'grp_val'
    df[GRP_VAL] = df['type'] + '_' + df['horizon']
    piv1 = df.pivot_table(index=['date'], columns=GRP_VAL, values='value', aggfunc='sum')
    piv2 = df.pivot_table(index=['date'], columns='type', values='value', aggfunc='sum')

    piv = piv1.join(piv2)
    piv[NE_COL] = piv[asset_col_name] - piv[liab_col_name]

    piv[NE_INTERP_COL] = piv[NE_COL].replace({0: np.nan}).interpolate()
    piv[ASSET_INTERP] = piv[asset_col_name].replace({0: np.nan}).interpolate()
    piv[LIAB_INTERP] = piv[liab_col_name].replace({0: np.nan}).interpolate()
    piv[DELTA_LIAB] = piv[LIAB_INTERP].diff()
    piv[DELTA_ASSET] = piv[ASSET_INTERP].diff()
    piv[DELTA_EQUITY] = piv[NE_INTERP_COL].diff()
    piv[CURRENT_RATIO] = piv[f"{asset_col_name}_long"] / piv[liab_col_name] - 1
    piv[QUICK_RATIO] = piv[f"{asset_col_name}_short"] / piv[liab_col_name]
    piv[VAL_ABOVE_LIAB] = piv[asset_col_name] / piv[liab_col_name] - 1
    piv[PERC_GAIN] = piv[DELTA_EQUITY] / piv[NE_INTERP_COL].shift(1)
    piv[EFF_APY] = (1 + piv[PERC_GAIN]) ** 12 - 1

    # piv[PROJECTED_NE_AT_MARR] = piv.apply(lambda x: _apply_ne_projections(piv.reset_index()[NE_INTERP_COL], x, marr))
    first_pos_idx_for_ne = (piv.reset_index()[NE_INTERP_COL] > 0).idxmax()
    first_positive_ne_value = piv[NE_INTERP_COL].iloc[first_pos_idx_for_ne]
    piv[PROJECTED_NE_AT_MARR] = [_project_at_rate(first_positive_ne_value, marr / 12.0, row_num - first_pos_idx_for_ne)
                                 if (row_num >= first_pos_idx_for_ne) else np.nan
                                 for row_num, (idx, row) in enumerate(piv.iterrows())]

    if echo:
        ph.pretty_print_dataframe(piv)
    piv = piv.reset_index()
    return piv


def asset_liab_ne_summarized(
        df,
        asset_col_name: str = ASSET_COL,
        liab_col_name: str = LIAB_COL,
        echo: bool = False,
        prevent_date_easy: bool = False
):
    df = ph.clean_a_dataframe(
        df=df,
        column_type_definition={
            'date': datetime.date,
            'category': str,
            'value': float,
            'type': str,
            'horizon': str
        }
    )

    if not prevent_date_easy:
        df['date'] = df['date'].dt.strftime("%Y-%m")

    piv = pivot_recorded_values(df)
    gpd = grouped_data(df, echo=False)
    return balance_sheet_summary(gpd,
                                 asset_col_name=asset_col_name,
                                 liab_col_name=liab_col_name,
                                 echo=False
                                 )


def fi_dataset_expanded(
        income_expense_df_provider: tp.DataFrameProvider,
        asset_liability_df_provider: tp.DataFrameProvider,
        end_date: datetime.date,
        stable_interest_rate: float = .05,
        income_expense_date_stamp_col_name: str = DATE_STAMP_COL,
        asset_liability_date_stamp_col_name=DATE_STAMP_COL,
        income_col_name: str = INCOME_COL,
        expense_col_name: str = EXPENSE_COL,
        asset_col_name: str = ASSET_COL,
        liab_col_name: str = LIAB_COL,
        ne_col_name: str = NE_COL,
        ne_interpoloated_col_name: str = NE_INTERP_COL,
        echo: bool = False,
        fi_target: float = None,
        fi_target_quantile: float = None,
) -> pd.DataFrame:
    income_exp_df = tp.resolve(income_expense_df_provider)
    income_exp_df = ph.clean_a_dataframe(
        df=income_exp_df,
        column_type_definition={
            income_expense_date_stamp_col_name: datetime.date,
            income_col_name: float,
            expense_col_name: float
        }
    )

    asset_liab_ne_df = tp.resolve(asset_liability_df_provider)
    asset_liab_ne_df = ph.clean_a_dataframe(
        df=asset_liab_ne_df,
        column_type_definition={
            asset_liability_date_stamp_col_name: datetime.date,
            asset_col_name: float,
            liab_col_name: float,
            ne_col_name: float,
            ne_interpoloated_col_name: float
        }
    )
    EOM_COL = 'eom'
    asset_liab_ne_df[EOM_COL] = asset_liab_ne_df[asset_liability_date_stamp_col_name].apply(
        lambda x: du.last_day_of_month(x))
    income_exp_df[EOM_COL] = income_exp_df[income_expense_date_stamp_col_name].apply(lambda x: du.last_day_of_month(x))

    df = income_exp_df.merge(asset_liab_ne_df, left_on=EOM_COL, right_on=EOM_COL)

    df[FI_MONTH_CASH_COL] = df.apply(
        func=lambda x: "" if x[ne_interpoloated_col_name] == "" \
            else x[ne_interpoloated_col_name] * stable_interest_rate / 12,
        axis=1
    )

    df['margin'] = df[income_col_name] - df[expense_col_name]
    df[AVG_6MO_EXP_COL] = df[expense_col_name].rolling(window=6).mean()
    df[AVG_6MO_INC_COL] = df[income_col_name].rolling(window=6).mean()
    df[AVG_INC_COL] = df[income_col_name].expanding().mean()
    df[AVG_EXP_COL] = df[expense_col_name].expanding().mean()
    df['avg_margin'] = df[AVG_INC_COL] - df[AVG_EXP_COL]
    df[AVG_6MO_MARGIN_COL] = df[AVG_6MO_INC_COL] - df[AVG_6MO_EXP_COL]
    df['perc_of_goal'] = df.apply(
        func=lambda x: "" if x[FI_MONTH_CASH_COL] == ""
        else x[FI_MONTH_CASH_COL] / x[AVG_6MO_EXP_COL],
        axis=1
    )
    df['pct_delta_avail_cap'] = df[ne_col_name].pct_change()
    df['delta_perc_of_goal'] = df['perc_of_goal'] / df['perc_of_goal'].shift(1) - 1

    DATE_CALC = 'date_calc'
    df = ph.include_rows_for_all_date_increment(
        df,
        datetime_column_name=asset_liability_date_stamp_col_name,
        datetime_increment_type=du.DateIncrementType.MONTH,
        end=du.datestamp_tryParse(end_date),
        out_date_column_name=DATE_CALC
    )

    # Project the fi cashflows thorugh end of date span
    last_valid_cashflow_idx = df[FI_MONTH_CASH_COL].last_valid_index()
    last_cashflow_val = df[FI_MONTH_CASH_COL].loc[last_valid_cashflow_idx]
    df[PROJECTED_FI_MONTH_CASH_COL] = df.apply(axis=1,
                                               func=lambda x: x[FI_MONTH_CASH_COL] if not np.isnan(x[FI_MONTH_CASH_COL]) \
                                                   else last_cashflow_val * (
                                                       1 + df['pct_delta_avail_cap'].median()) ** (
                                                                x.name - last_valid_cashflow_idx))

    # Extend the values for avg income, expense, and margin through the end of the dataframe
    cols = [AVG_6MO_INC_COL, AVG_6MO_EXP_COL, AVG_6MO_MARGIN_COL]
    df.loc[:, cols] = df.loc[:, cols].ffill()

    if fi_target is None and fi_target_quantile is None:
        fi_target = df[AVG_6MO_EXP_COL].values[-1:][0]

    if fi_target is None and fi_target_quantile is not None:
        fi_target = df[expense_col_name].quantile(fi_target_quantile)

    df[FI_TARGET_COL] = fi_target

    if echo:
        ph.pretty_print_dataframe(df)

    df[DATE_CALC_STR] = df[DATE_CALC].dt.strftime('%Y-%m')

    return df


def fi_pyplot(
        ax,
        df_provider: tp.DataFrameProvider,
        income_col_name: str = INCOME_COL,
        expense_col_name: str = EXPENSE_COL,
        stable_interest_rate: float = 0.05,
        fill_alpha: float = 0.15,
        x_tick_font: Dict = {'size': 6},
        echo: bool = False
):
    df = tp.resolve(df_provider)

    fi_target = df[FI_TARGET_COL][0]

    subtitle_txt = f"FI Target is {DOLLAR_FMT.format(fi_target)} which would require {DOLLAR_FMT.format(fi_target / (stable_interest_rate / 12))} in available funds to generate at an {round(stable_interest_rate * 100, 2)}% APY"
    if echo:
        print(subtitle_txt)

    last_projected_cashflow = df[PROJECTED_FI_MONTH_CASH_COL].values[-1]
    fi_label = f"${DOLLAR_FMT.format(last_projected_cashflow)} ({round(last_projected_cashflow / fi_target * 100, 1)}%)"
    target_label = f"${DOLLAR_FMT.format(fi_target)}"
    avg_margin_label = f"${DOLLAR_FMT.format(df[AVG_6MO_MARGIN_COL].values[-1])}"
    avg_income_label = f"${DOLLAR_FMT.format(df[AVG_6MO_INC_COL].values[-1])}"
    avg_exp_label = f"${DOLLAR_FMT.format(df[AVG_6MO_EXP_COL].values[-1])}"

    plot_args = {
        AVG_6MO_EXP_COL: cplt.PlotArgs(
            color=Color.RED,
            linestyle='--',
            linewidth=.5,
            labels={df[DATE_CALC_STR].values[-1:][0]: avg_exp_label}
        ),
        AVG_6MO_INC_COL: cplt.PlotArgs(
            color=Color.GREEN,
            linestyle='--',
            linewidth=.5,
            labels={df[DATE_CALC_STR].values[-1:][0]: avg_income_label}
        ),
        AVG_6MO_MARGIN_COL: cplt.PlotArgs(
            color=Color.PURPLE,
            linestyle='--',
            linewidth=.5,
            labels={df[DATE_CALC_STR].values[-1:][0]: avg_margin_label}
        ),
        'margin': cplt.PlotArgs(
            color=Color.PURPLE,
            linestyle='-',
            linewidth=.5
        ),
        FI_MONTH_CASH_COL: cplt.PlotArgs(
            color=Color.GOLD,
            linestyle='-',
            linewidth=1
        ),
        expense_col_name: cplt.PlotArgs(
            color=Color.RED,
            linestyle='-',
            linewidth=1
        ),
        income_col_name: cplt.PlotArgs(
            color=Color.GREEN,
            linestyle='-',
            linewidth=1
        ),
        PROJECTED_FI_MONTH_CASH_COL: cplt.PlotArgs(
            color=Color.GOLD,
            linestyle='--',
            linewidth=.5,
            labels={df[DATE_CALC_STR].values[-1:][0]: fi_label}
        ),
        FI_TARGET_COL: cplt.PlotArgs(
            color=Color.TEAL,
            linestyle='-.',
            linewidth=3,
            labels={df[DATE_CALC_STR].values[-1:][0]: target_label}
        ),
    }

    ph.plot(
        df=df,
        x_column_name=DATE_CALC_STR,
        plottables=plot_args,
        ax=ax
    )

    ax.fill_between(df[DATE_CALC_STR], df[income_col_name], df[expense_col_name], color='red',
                    where=(df[expense_col_name] > df[income_col_name]),
                    alpha=fill_alpha,
                    interpolate=True)
    ax.fill_between(df[DATE_CALC_STR], df[income_col_name], df[expense_col_name], color='green',
                    where=(df[income_col_name] > df[expense_col_name]),
                    alpha=fill_alpha,
                    interpolate=True)
    ax.set_xticklabels(df[DATE_CALC_STR], rotation=45, fontsize=x_tick_font['size'])
    font1 = {'family': 'serif', 'color': 'blue', 'size': 20}
    font2 = {'family': 'serif', 'color': 'darkred', 'size': 15}

    ax.set_title("FI Trends", fontdict=font1)
    # Add a subtitle to the entire figure
    plt.figtext(s=subtitle_txt, fontsize=10, x=0.5, y=0.01, ha='center')

    ax.set_xlabel("", fontdict=font2)
    ax.set_ylabel("$", fontdict=font2)
    ax.legend([x for x in plot_args.keys()], )
    ax.axhline(0, c='k')
    ax.xaxis.grid(True, color='grey', linestyle='--', linewidth=0.5)


if __name__ == "__main__":
    def dummy_data():
        return pd.DataFrame(
            {'account': [
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A1',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2',
                'A2'],
                'from_subaccount_name': [
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    '-',
                    'Chatham',
                    'Chatham',
                    '-',
                    'Chatham',
                    'Chatham',
                    '-',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    'Chatham',
                    '-',
                    'Chatham',
                    '-',
                    'Chatham'],
                'spend_category_at_time_of_record':
                    [
                        'RENT_MORTGAGE',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'ADMINISTRATION',
                        'MAINTENANCE',
                        'RENT_MORTGAGE',
                        'ADMINISTRATION',
                        'MAINTENANCE',
                        'PROPERTY_MANAGEMENT',
                        'ADMINISTRATION',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'RENT_MORTGAGE',
                        'PROPERTY_MANAGEMENT',
                        'ADMINISTRATION',
                        'UTILITIES',
                        'ADMINISTRATION',
                        'RENT_MORTGAGE',
                    ],
                'ledger_date_stamp':
                    [
                        '10/3/2024',
                        '9/3/2024',
                        '8/30/2024',
                        '8/5/2024',
                        '7/31/2024',
                        '7/3/2024',
                        '6/25/2024',
                        '6/3/2024',
                        '5/31/2024',
                        '5/3/2024',
                        '4/30/2024',
                        '4/12/2024',
                        '4/3/2024',
                        '4/3/2024',
                        '3/29/2024',
                        '3/26/2024',
                        '3/24/2024',
                        '3/8/2024',
                        '3/4/2024',
                        '2/29/2024',
                        '2/5/2024',
                        '1/31/2024',
                        '1/11/2024',
                        '1/8/2024',
                        '1/5/2024',
                        '1/3/2024',
                    ],
                'amount':
                    [
                        '963.87',
                        '963.87',
                        '119.5',
                        '963.87',
                        '119.5',
                        '963.87',
                        '119.5',
                        '963.87',
                        '119.5',
                        '963.87',
                        '119.5',
                        '131.88',
                        '1112',
                        '963.87',
                        '150',
                        '664',
                        '119.5',
                        '18.48',
                        '963.87',
                        '119.5',
                        '970.46',
                        '119.5',
                        '94.57',
                        '79.98',
                        '26.52',
                        '942.27']
            }
        )


    def t_pivot_01():
        df = amount_pivot(
            history_df_provider=dummy_data(),
            grouped_history_type=PivotProfileType.ACCOUNT_SUBACCOUNT_CATEGORY__DATESTAMP,
            account_col_name='account',
            subaccount_col_name='from_subaccount_name',
            category_col_name='spend_category_at_time_of_record',
            date_stamp_col_name='ledger_date_stamp'

        )
        ph.pretty_print_dataframe(
            ph.summary_rows_cols(df,
                                 row_sum=True,
                                 row_avg=True,
                                 row_median=True,
                                 column_sum=True,
                                 column_avg=True,
                                 na_fill='-',
                                 replace_zero_val='-'),
            float_format='%.2f')


    def t_fi_01():
        dates = [
            '10/3/2024',
            '9/3/2024',
            '8/30/2024',
            '8/5/2024',
            '7/31/2024',
            '7/3/2024',
            '6/25/2024',
            '6/3/2024',
            '5/31/2024',
            '5/3/2024',
            '4/30/2024',
            '4/12/2024',
            '4/3/2024',
            '4/3/2024',
            '3/29/2024',
        ]
        dates.reverse()

        fi_pyplot(
            echo=True,
            end_date=du.datestamp_tryParse('5/15/25'),
            history_df_provider=pd.DataFrame(
                data={
                    DATE_STAMP_COL: dates,
                    INCOME_COL: [
                        13411.49,
                        14380.03,
                        11937.44,
                        11345.97,
                        13031.21,
                        11868.40,
                        12751.79,
                        16346.99,
                        19951.46,
                        19018.84,
                        19703.26,
                        10213.50,
                        12890.43,
                        13656.81,
                        12814.61,
                    ],
                    EXPENSE_COL: [
                        9645.43,
                        11547.92,
                        9373.37,
                        11354.97,
                        8604.08,
                        12370.98,
                        11410.12,
                        17101.60,
                        11717.44,
                        13469.02,
                        10768.87,
                        8062.03,
                        12899.59,
                        12047.84,
                        12160.03,
                    ],
                    AVAIL_CAP_COL: [
                        50907.76,
                        53024.04,
                        59755.11,
                        63798.82,
                        70329.91,
                        81542.45,
                        88915.60,
                        102896.92,
                        133593.26,
                        188941.09,
                        201128.88,
                        214479.32,
                        220956.98,
                        233913.01,
                        239324.96,
                    ]
                }
            )
        )


    def t_fi_02():
        fix, ax = plt.subplots()
        df = pd.read_csv(r"C:\Users\Tj Burns\Downloads\fi_data_2505.txt", delimiter='\t')
        # fi_graph(
        #     ax=ax,
        #     history_df_provider=df,
        #     end_date=du.date_tryParse('12/1/26'),
        #     date_stamp_col_name='date_stamp',
        #     avail_cap_col_name='AvailableCapital',
        #     echo=True,
        #     # fi_target=15000,
        #     fi_target_quantile=0.5,
        # )

    # t_pivot_01()
    # t_fi_01()
    t_fi_02()