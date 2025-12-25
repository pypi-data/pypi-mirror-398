import pandas as pd
from typing import Dict, Callable, List
import datetime
from cooptools.printing import pretty_format_list_of_tuple, pretty_format_dataframe
import numpy as np
import cooptools.date_utils as date_utils
from cooptools.common import cross_apply
from cooptools import typeProviders as tp
import logging
from cooptools import plotting as coopplt
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class PandasMissingColumnsException(Exception):
    ''' Raised when a user tries to create an account that already exists'''

    def __init__(self, columns_present: List[str], required_columns: List[str]):
        self.columns_present = columns_present
        self.required_columns = required_columns
        self.missing_columns = list(set(required_columns) - set(columns_present))
        self.message = f"All columns [{self.required_columns}] required but columns [{self.missing_columns}] were missing. Present columns: [{columns_present}]"
        super().__init__(self.message)


class PandasFillColumnTypeException(Exception):
    def __init__(self, str):
        Exception().__init__(str)

    pass


def summary_rows_cols(df: pd.DataFrame,
                      column_sum: bool = False,
                      column_avg: bool = False,
                      column_median: bool = False,
                      row_sum: bool = False,
                      row_avg: bool = False,
                      row_median: bool = False,
                      na_fill: str = None,
                      replace_zero_val: str = None,
                      sig_digs: int = 3,
                      sort_rows_by_sum: bool = False
                      ) -> pd.DataFrame:
    ret = df.copy()

    # Optional: Sort rows by sum before adding any column aggregates
    if sort_rows_by_sum:
        row_sums = ret.sum(axis=1, numeric_only=True)
        ret = ret.loc[row_sums.sort_values(ascending=False).index]

    # column sums based on the original dataframe
    if column_sum: ret.loc['Sum'] = df.sum(numeric_only=True, axis=0, min_count=1).round(sig_digs)
    if column_avg: ret.loc['Avg'] = df.mean(numeric_only=True, axis=0).round(sig_digs)
    if column_median: ret.loc['Median'] = df.median(numeric_only=True, axis=0, min_count=1).round(sig_digs)

    # row sums on the new dataframe as to accommodate "summing the sums", first calculate the values
    sum = None
    median = None
    avg = None
    if row_sum: sum = ret.sum(numeric_only=True, axis=1).round(sig_digs)
    if row_avg: avg = ret.mean(numeric_only=True, axis=1).round(sig_digs)
    if row_median: median = ret.median(numeric_only=True, axis=1).round(sig_digs)

    # then, append them to the end of the dataframe (RHS)
    if sum is not None: ret.loc[:, 'Sum'] = sum
    if avg is not None: ret.loc[:, 'Avg'] = avg
    if median is not None: ret.loc[:, 'Median'] = median

    if na_fill is not None:
        ret.fillna(na_fill, inplace=True)

    if replace_zero_val is not None:
        ret.replace(to_replace=0, value=replace_zero_val, inplace=True)

    return ret


def pretty_print_dataframe(df: pd.DataFrame, title: str = None,
                           display_width: int = 2000,
                           display_max_columns: int = 2000,
                           display_max_column_width: int = None,
                           display_max_rows: int = 500,
                           float_format: str = '%.3f',
                           prevent_newline_bool=False,
                           **kwargs
                           ):
    ret = ""

    if title:
        ret += title
        print(title)

    with pd.option_context('display.max_rows', display_max_rows,
                           'display.max_columns', display_max_columns,
                           'display.max_colwidth', display_max_column_width,
                           'display.width', display_width,
                           'display.float_format', lambda x: float_format % x):
        ret += f"{df}\n"
        nl_txt = "" if prevent_newline_bool else "\n"
        print(f"{df}{nl_txt}")

    return ret


def find_the_type_conversion_errors_and_raise(df: pd.DataFrame, column_type_definition: Dict):
    errors = []
    for column, requested_type in column_type_definition.items():
        try:
            df[column].astype(requested_type)
        except:
            for index, row in df.iterrows():
                try:
                    row[column].astype(requested_type)
                except:
                    errors.append((index, column, f"\"{row[column]}\"", requested_type, type(row[column])))

    errors_df = pd.DataFrame(errors,
                             columns=['row_index', 'column_name', 'value', 'requested_type_conversion', 'current_type'])

    raise ValueError(f"Error performing the following conversions: \n{pretty_format_dataframe(errors_df)}")


def clean_currency(x):
    """ If the value is a string, then remove currency symbol and delimiters
    otherwise, the value is numeric and can be converted
    """
    if isinstance(x, str):
        return (x.replace('$', '').replace(',', '').replace('(', '-').replace(')', ''))
    return (x)


def convert_pandas_data_columns_to_type(df: pd.DataFrame, column_type_definition: Dict) -> pd.DataFrame:
    if df is None:
        return None

    # handle currency conversions for floats/ints:
    columns_that_may_need_cleaned = [k for k, v in column_type_definition.items() if
                                     v in (float, int) and k in df.columns]
    for column in columns_that_may_need_cleaned:
        pd.options.mode.chained_assignment = None
        df[column] = df[column].map(clean_currency)
        pd.options.mode.chained_assignment = 'warn'

    # Cast columns as type (excluding dates and ints)
    types = {k: v for k, v in column_type_definition.items() if
             v not in (datetime.date, datetime.datetime) and k in df.columns}
    try:
        df = df.astype(types)
    except:
        find_the_type_conversion_errors_and_raise(df[[x for x in types.keys()]], types)

    # handle date conversions
    for col, type in {k: v for k, v in column_type_definition.items() if
                      v in (datetime.date, datetime.datetime) and k in df.columns}.items():
        df[col] = try_parse_and_localize_date_series(df[col],
                                                     type=type)

    return df


def verify_all_required_columns(df: pd.DataFrame, required_columns: List[str]):
    if not all(column in df.columns for column in required_columns):
        raise PandasMissingColumnsException(columns_present=[col for col in df.columns],
                                            required_columns=required_columns)


def replace_column_names(df: pd.DataFrame,
                         column_name_replacement: Callable[[pd.DataFrame], Dict] | Dict = None):
    ret = df.copy()

    if column_name_replacement is None:
        return ret
    elif type(column_name_replacement) == dict:
        return ret.rename(columns=column_name_replacement)
    elif callable(column_name_replacement):
        return ret.rename(columns=column_name_replacement(ret))

    raise ValueError(f"Unhandled column name replacement situation: "
                     f"\n{ret}"
                     f"\n{type(column_name_replacement)}")


def clean_a_dataframe(df: pd.DataFrame,
                      column_type_definition: Dict,
                      case_sensitive: bool = False,
                      allow_partial_columnset: bool = False,
                      fill_missing: bool = False,
                      column_name_replacement: Callable[[pd.DataFrame], Dict] | Dict = None,
                      keep_extra: bool = False,
                      nan_replacements: Dict = None) -> pd.DataFrame:
    required_columns = [key for key, value in column_type_definition.items()]

    # map columns that dont match name
    df = replace_column_names(df=df,
                              column_name_replacement=column_name_replacement)

    # update based on case-sensitivity
    if not case_sensitive:
        df.columns = map(str.lower, df.columns)
        col_indexes = {col: df.columns.get_loc(col.lower()) if col.lower() in df.columns else None for col in
                       required_columns}
        name_replacements = {[x for x in df.columns][ind]: col for col, ind in col_indexes.items() if ind is not None}
        df.rename(columns=name_replacements, inplace=True)

    # Filter columns
    if not keep_extra:
        df = df[[col for col in required_columns if col in df.columns]]

    # raise error if not all columns exist
    if not allow_partial_columnset:
        verify_all_required_columns(df, required_columns)

    # handle empty dataframe
    if not any(df):
        df = pd.DataFrame(columns=required_columns)

    # add missing columns
    missing_columns = [column for column in required_columns if column not in df.columns]
    if fill_missing:
        for col in missing_columns:
            requested_type = column_type_definition[col]
            if requested_type in [int]:
                raise PandasFillColumnTypeException(
                    f"Unable to create an empty column of type {requested_type}. {requested_type} is not nullable.")
            df[col] = pd.Series([], dtype=requested_type)

    # replace nans:
    if nan_replacements:
        for column, replacement in nan_replacements.items():
            df[column] = df[column].replace(np.nan, replacement)

    # column type conversions
    df = convert_pandas_data_columns_to_type(df, column_type_definition)

    # return
    return df


def try_parse_and_localize_date_series(date_column,
                                       type: [datetime.date, datetime.datetime]):
    if type == datetime.datetime:
        date_column = date_column.apply(lambda x: date_utils.datestamp_tryParse(x))
    if type == datetime.date:
        date_column = date_column.apply(lambda x: date_utils.date_tryParse(x))
    try:
        return pd.to_datetime(date_column).dt.tz_localize(None)
    except:
        return pd.to_datetime(date_column)


def import_data(
        file_path_provider: tp.FilePathProvider,
        column_type_definition: Dict = None,
        column_name_replacements: Dict = None,
        allow_partial: bool = False,
        fill_missing: bool = False,
        echo: bool = False
) -> pd.DataFrame:
    file_path = tp.resolve_filepath(file_path_provider)

    logger.info(f"Reading data from {file_path}")

    df = pd.read_csv(file_path)
    if df is None:
        return None

    if column_type_definition:
        df = clean_a_dataframe(df,
                               column_type_definition=column_type_definition,
                               allow_partial_columnset=allow_partial,
                               column_name_replacement=column_name_replacements,
                               fill_missing=fill_missing)

    if echo:
        pretty_print_dataframe(df)

    return df


def import_data_from_csv_with_specified_columns(column_type_definition: Dict,
                                                file_path: str = None,
                                                file_path_provider: tp.FilePathProvider = None,
                                                allow_partial: bool = False,
                                                fill_missing: bool = False,

                                                echo_rows: int = None) -> pd.DataFrame:
    if file_path is None and file_path_provider is None:
        e = f"At least one of filepath and filepath_provider must not be none"
        logger.error(e)
        raise ValueError(e)

    df = import_data(
        file_path_provider=file_path_provider or file_path,
        column_type_definition=column_type_definition,
        allow_partial=allow_partial,
        fill_missing=fill_missing
    )
    if df is None:
        return None

    return df


column_date_ge_filter = lambda df, col_name, val: df[col_name] >= val
column_date_le_filter = lambda df, col_name, val: df[col_name] <= val
column_date_bet_filter = lambda df, col_name, small, large: small <= df[col_name] <= large


def _clean_state_change_data(df: pd.DataFrame,
                             datetime_column: str,
                             state_column: str,
                             partition_column: str = None,
                             start: datetime.datetime = None,
                             end: datetime.datetime = None):
    # handle init-ing the provided values that were None
    if start is None:
        start = np.datetime64(df[datetime_column].min())

    if end is None:
        end = np.datetime64(df[datetime_column].max())

    # create a working copy of the input dataframe
    working_df = df.copy()

    # need to only keep the records between the start and end times. However, we would like to keep the last record
    # immediately prior to the time frame if it exists. This is because we want to account for the state leading into
    # the start-end time range. This allows us to account for all the time we can. We achieve this by first sorting
    # the dataframe by partition/datetime. Then setting the dates = start if the date < start. We then drop the
    # duplicates so that there is only one record remaining. This will not hurt the records within the range either
    # as we would have no better option for handling two distinct states at the same time
    working_df.sort_values(by=[partition_column, datetime_column], inplace=True)
    working_df[datetime_column] = np.where(working_df[datetime_column] < start, start, working_df[datetime_column])
    working_df.drop_duplicates(subset=[partition_column, datetime_column], keep='last')
    working_df[datetime_column] = np.where(working_df[datetime_column] > end, end, working_df[datetime_column])

    # Enusre there is a record for all partitions at start. This is bc we use the diff() function later to aggregate the
    # amount of time in each state. If there isnt a record at start, the time will be off. We do this by grouping the
    # dataframe based on partition, and looking at the first entry. If the first entry is greater than the start value,
    # then we need introduce a new dummy record at start.
    inserts_min = working_df.groupby([partition_column]).first().reset_index()
    inserts_min = inserts_min[inserts_min[datetime_column] > start]
    inserts_min[state_column] = 'UNK_START'
    inserts_min[datetime_column] = start

    # Similiarly, we need to ensure there is a record for all partitions at end. This is bc we use the diff() function
    # later to aggregate the amount of time in each state. If there isnt a record at end, the time will be off. We do
    # this by grouping the dataframe based on partition, and looking at the last entry. If the last entry is less than
    # the end value, then we need introduce a new dummy record at end.
    inserts_max = working_df.groupby([partition_column]).last().reset_index()
    inserts_max = inserts_max[inserts_max[datetime_column] < end]
    inserts_max[datetime_column] = end
    inserts_max[state_column] = 'END'

    # add the inserts to the working df
    working_df = pd.concat([inserts_min, inserts_max, working_df], ignore_index=True, axis=0)

    # determine the partition ranks for evaluating if the states changed. While it would technically still calculate
    # correctly, some of the output options will be cleaner if there is only one record for non-duplicate state changes.
    # we do this by creating a rank based on the state and partition (sort first to be sure its in the right order). If
    # there are duplicates, we want only the min entry. We can check if the value has cahnged by using the diff() func
    # on the column we just created. If the diff is positive, there was a change. We only keep the records where there
    # was a change. For clairity, we also create a column indicating the row within the partition after trimming the
    # duplicates.
    working_df.sort_values(by=[partition_column, datetime_column], inplace=True)
    working_df['change_rank_partition'] = working_df[[state_column, partition_column]].apply(tuple, axis=1).rank(
        method='min')
    working_df['changed'] = np.where(working_df['change_rank_partition'].diff() != 0, 1, 0)
    working_df = working_df[working_df['changed'] == 1]
    working_df['local_row'] = working_df.groupby([partition_column])[datetime_column].rank(method='min')

    # calculate the delta times between records. We use the where() func to make sure we calculate a 0 for switching
    # between partitions. O.w, a simple diff of the values (next-this). The math for time between pandas and numpy is
    # terrible, so do an explicit conversion to get it into integer minutes.
    working_df['date_diff_minute'] = np.where(
        working_df[partition_column].shift(periods=-1) != working_df[partition_column],
        0,
        -working_df[datetime_column].diff(periods=-1) / np.timedelta64(1, 'm'))

    # now that we've used the diff() function, we no longer need the 'END' record. drop it
    return working_df[working_df[state_column] != 'END']


def df_join_all_dates(df: pd.DataFrame,
                      concat_columns: List[str],
                      out_date_column_name: str = None,
                      start: datetime.datetime = None,
                      end: datetime.datetime = None,
                      datetime_increment_type: date_utils.DateIncrementType = date_utils.DateIncrementType.HOUR,
                      agg_map: Dict[str, List[str]] = None
                      ) -> pd.DataFrame:
    # init values
    if out_date_column_name is None:
        out_date_column_name = 'date_calc'

    if start is None:
        start = np.datetime64(df[concat_columns[0]].min())

    if end is None:
        end = np.datetime64(df[concat_columns[0]].max())

    if agg_map is None:
        agg_map = {x: ['count'] for x in list(df.columns) if x not in concat_columns}

    # create a list of dates in the provided date range
    all_dates = date_utils.datetime_range(start_date_time=start, end_date_time=end,
                                          increment_type=datetime_increment_type)

    # create a dataframe of the concatendated dates with all of the provided columns to be concatendated
    concat_values = [all_dates] + [df[x].unique().tolist() for x in concat_columns[1:]]
    left_df = pd.DataFrame(cross_apply(concat_values),
                           columns=[out_date_column_name] + concat_columns[1:])

    # group the data based on the datetime incrememnt to be joined back to the concatendated data
    right_df = df
    right_df[concat_columns[0]] = date_utils.bucket_datestamp(right_df[concat_columns[0]], datetime_increment_type)
    right_df = df.groupby(concat_columns).agg(
        {x: agg_map[x] for x in list(df.columns) if x not in concat_columns}).reset_index()

    # join the left and right dfs
    working_df = pd.merge(left_df, right_df.droplevel(1, axis=1), left_on=list(left_df.columns),
                          right_on=concat_columns, how='left').fillna(0).sort_values(
        by=concat_columns[1:] + [out_date_column_name])
    ret = working_df[[x for x in working_df.columns if x != tuple([concat_columns[0], ''])]]

    ret.reset_index(inplace=True)
    return ret


def include_rows_for_all_date_increment(
        df: pd.DataFrame,
        datetime_column_name: str,
        start: datetime.datetime = None,
        end: datetime.datetime = None,
        datetime_increment_type: date_utils.DateIncrementType = date_utils.DateIncrementType.HOUR,
        out_date_column_name: str = None,
):
    # init values
    if out_date_column_name is None:
        out_date_column_name = 'date_calc'

    if start is None:
        start = np.datetime64(df[datetime_column_name].min())

    if end is None:
        end = np.datetime64(df[datetime_column_name].max())

    all_dates = date_utils.datetime_range(
        start_date_time=start,
        end_date_time=end,
        increment_type=datetime_increment_type
    )

    left_df = pd.DataFrame(
        all_dates,
        columns=[out_date_column_name]
    )

    right_df = df
    right_df['date_bucketed'] = date_utils.bucket_datestamp(
        right_df[datetime_column_name],
        datetime_increment_type
    )

    right_df = right_df.sort_values(by=[datetime_column_name])
    right_df.drop_duplicates(['date_bucketed'], keep='first')

    working_df = pd.merge(
        left_df,
        right_df,
        left_on=out_date_column_name,
        right_on='date_bucketed',
        how='left').sort_values(by=out_date_column_name)

    working_df.reset_index(inplace=True)

    return working_df


def state_change_data(df: pd.DataFrame,
                      datetime_column: str,
                      state_column: str,
                      partition_column: str = None,
                      start: datetime.datetime = None,
                      end: datetime.datetime = None,
                      partition_summary_pivot: bool = False,
                      agg_over_time: bool = False,
                      datetime_increment_type: date_utils.DateIncrementType = date_utils.DateIncrementType.HOUR):
    # init some vars
    if datetime_increment_type is None:
        datetime_increment_type = date_utils.DateIncrementType.HOUR

    # clean the input dataframe
    clean = _clean_state_change_data(df,
                                     datetime_column=datetime_column,
                                     state_column=state_column,
                                     partition_column=partition_column,
                                     start=start,
                                     end=end)

    #pivot return type
    if partition_summary_pivot == True:
        return pd.pivot_table(clean, index=[partition_column], columns=[state_column], values=['date_diff_minute'],
                              fill_value=0)

    #agg over time return type
    if agg_over_time == True:
        all_dates = date_utils.datetime_range(start_date_time=start, end_date_time=end,
                                              increment_type=datetime_increment_type)
        new_date_col = 'date_calc'

        concat_df = pd.DataFrame(cross_apply([clean[partition_column].unique().tolist(), all_dates]),
                                 columns=[partition_column, new_date_col])
        clean[datetime_column] = date_utils.bucket_datestamp(clean[datetime_column], datetime_increment_type)
        working_df = pd.merge(concat_df, clean, left_on=[new_date_col, partition_column],
                              right_on=[datetime_column, partition_column], how='left').fillna(method='ffill')
        working_df = working_df[[partition_column, new_date_col, state_column]]

        state_changed = working_df[state_column].ne(working_df[state_column].shift().bfill()).astype(int)
        partition_changed = working_df[state_column].ne(working_df[state_column].shift().bfill()).astype(int)
        changed = (state_changed + partition_changed).to_frame()
        changed.iloc[0][state_column] = 1

        changed = changed[state_column].apply(lambda x: 1 if x > 0 else 0)
        pretty_print_dataframe(changed)

        working_df['changed'] = changed
        return working_df

    # default return the working_df as is
    return clean


def plot(
        df: pd.DataFrame,
        x_column_name: str,
        plottables: Dict[str, coopplt.PlotArgs],
        ax: plt.axes = None
):
    if ax is None:
        ax = plt

    for column, args in plottables.items():
        line, = ax.plot(df[x_column_name],
                        df[column],
                        color=tuple(x / 255.0 for x in args.color.value) if args.color is not None else None,
                        linestyle=args.linestyle,
                        linewidth=args.linewidth)

        if args.labels is not None:
            _lbls = {str(k): (k, v) for k, v in args.labels.items()}

            idx_map = {str(df[x_column_name].values[idx]): idx for idx, row in df.iterrows()}

            for str_x_val, x__lbl in _lbls.items():
                x, lbl = x__lbl
                y = float(df[column][idx_map[str_x_val]])

                ax.annotate(lbl,
                            xy=(x, y),
                            xytext=(5, -5),
                            textcoords='offset points', family='sans-serif', fontsize=8)


            #
            # for idx, row in df.iterrows():
            #     x = row[x_column_name]
            #     y = row[column]
            #
            #     x_str = str(df[x_column_name].values[idx])
            #     lbl = _lbls.get(x_str, '')
            #     ax.annotate(lbl,
            #                 xy=(x, y),
            #                 xytext=(5, -5),
            #                 textcoords='offset points', family='sans-serif', fontsize=8)


if __name__ == "__main__":
    # TEST 1
    # df = pd.read_csv('../tests/testdata/dummy_data_clean.csv')
    # column_definitions = {"my_clean_int": int,
    #                       "my_clean_str": str,
    #                       "my_clean_date": datetime.date,
    #                       "my_missing_column": np.int64}
    #
    # converted = clean_a_dataframe(df, column_type_definition=column_definitions, allow_partial_columnset=True)
    #
    # converted['newdate'] = converted['my_clean_date'] + datetime.timedelta(days=1)
    #
    # print(converted.dtypes)
    #
    #
    #
    # print(converted.dtypes['my_clean_date'])
    # print(converted.dtypes['my_clean_date'] == np.datetime64)
    # print(converted)

    # TEST Summary_rows_cols
    # data = {
    #     'a': [1, 2, 3],
    #     'b': [4, 5, 6],
    #     'c': [7, 8, 9]
    # }
    #
    # df = pd.DataFrame(data)
    #
    # printable = summary_rows_cols(df, row_sum=True, column_sum=True, row_median=True)
    #
    # pretty_print_dataframe(printable)

    # TEST STATUS CHANGED
    from randoms import random_datetime, LETTERS, NUMBERS
    import random as rnd

    rnd.seed(0)
    df = pd.DataFrame(
        data=[{'date': random_datetime(start_date=datetime.datetime.today().replace(hour=0, minute=0),
                                       end_date=datetime.datetime.now()),
               'state': rnd.choice(LETTERS[0:5]),
               'partition': rnd.choice(NUMBERS[0:2])} for x in range(10)]
    )

    pretty_print_dataframe(df_join_all_dates(df, ['date', 'partition']))

    # ret = state_change_data(df=df,
    #                   state_column='state',
    #                   datetime_column='date',
    #                   partition_column='partition',
    #                   partition_summary_pivot=False,
    #                   agg_over_time=True)
    # pretty_print_dataframe(ret)
