from typing import Dict, List, Union, Any, Callable
import numpy as np
from cooptools.trends import *
import math

def n_of_x_outside_mean_and_stdev(data,
                                  start,
                                  stop,
                                  mean,
                                  stdev,
                                  n_stdevs,
                                  x,
                                  n_of,
                                  high_low_both: int = None,
                                  outside: bool = True):

    if math.isclose(high_low_both, 0) or high_low_both is None:
        compare = lambda k: k < mean - n_stdevs * stdev or k > mean + n_stdevs * stdev
    elif high_low_both < 0: compare = lambda k: k < mean - n_stdevs * stdev
    elif high_low_both > 0: compare = lambda k: k > mean + n_stdevs * stdev
    else: raise ValueError(f"Unable to handle high_low_both value {high_low_both}")

    if not outside:
        _compare = lambda x: not compare(x)
    else:
        _compare = compare

    return qualify_data_points(data, start, stop, x, n_of, _compare)


def qualify_data_points(data,
                        start,
                        stop,
                        x,
                        n_of,
                        compare: Callable[[Union[float, int]], bool] = None):
    rule_triggers = []

    for ii in range(start + x - 1, stop):
        qualifiers = [x for x in data[ii - x + 1: ii + 1] if compare(x)]
        if len(qualifiers) >= n_of:
            rule_triggers.append([jj for jj in range(ii - x + 1, ii + 1)])

    return rule_triggers

def qualify_data_sequence(data,
                       start,
                       stop,
                       x,
                       compare: Callable[[List[Union[float, int]]], bool] = None):
    rule_triggers = []

    for ii in range(start + x - 1, stop):
        qualifiers = data[ii - x + 1: ii + 1] if compare(data[ii - x + 1: ii + 1]) else None
        if qualifiers is not None:
            rule_triggers.append([jj for jj in range(ii - x + 1, ii + 1)])

    return rule_triggers


def list_from_lists(lists_of_lists: List[List]):
    the_set = set()

    for alist in lists_of_lists:
        if alist is not None:
            try:
                the_set.update(list_from_lists(alist))
            except Exception as e:
                the_set.update(alist)
    return list(the_set)


def control(data: List[Union[int, float]],
            set_baseline_periods: int = None,
            trailing_window: int = None) -> List[Dict[str, Any]]:
    """ Takes a set of data and determines if it statistically in control

    :param: data: List of integers or floats that represents the data set to evaluate
    :param: set_baseline_periods: The number of periods that must pass before evaluating the statistics
    :param: trailing_window: The amount of past periods to evaluate for control (should be at least 15 since control includes
     checks of at least past 15 periods
    :return: List Dict of values by period
    """

    # init optional params
    if set_baseline_periods is None:
        set_baseline_periods = 20

    if trailing_window is None:
        trailing_window = 20

    if trailing_window <= 0:
        raise ValueError(f"The trailing window must be greater than zero. Ideally, this value is at least 20")

    # init the tracking dicts
    deltas = {}
    stdevs = {}
    means = {}
    medians = {}
    p_one_stdev = {}
    p_two_stdev = {}
    m_one_stdev = {}
    m_two_stdev = {}
    lcls = {}
    ucls = {}
    out_of_limit_high = {}
    out_of_limit_low = {}
    two_of_three_high_2stdev = {}
    two_of_three_low_2stdev = {}
    four_of_five_high_1stdev = {}
    four_of_five_low_1stdev = {}
    seven_high = {}
    seven_low = {}
    seven_trend_high = {}
    seven_trend_low = {}
    eight_out_of_1stdev = {}
    fifteen_within_1stdev = {}
    fourteen_alternate = {}
    out_of_control_triggering_points = {}
    out_of_control = {}

    # iterate the data
    for ii in range(0, len(data)):
        # track deltas
        deltas[ii] = data[ii] - data[ii-1] if ii > 0 else None

        # track means and stdevs
        start_period = max(0, ii - trailing_window - 1)
        means[ii] = round(np.mean(data[start_period: ii]), 3) if ii >= set_baseline_periods - 1 else None
        stdevs[ii] = round(np.std(data[start_period:ii]), 3) if ii >= set_baseline_periods - 1 else None
        medians[ii] = round(np.median(data[start_period:ii]), 3) if ii >= set_baseline_periods - 1 else None

        # track LCL and UCL, and stdev lvls
        lcls[ii] = (means[ii] - 3 * stdevs[ii]) if ii >= set_baseline_periods - 1 else None
        ucls[ii] = means[ii] + 3 * stdevs[ii] if ii >= set_baseline_periods - 1 else None
        p_one_stdev[ii] = means[ii] + stdevs[ii] if ii >= set_baseline_periods - 1 else None
        p_two_stdev[ii] = means[ii] + 2 * stdevs[ii] if ii >= set_baseline_periods - 1 else None
        m_one_stdev[ii] = means[ii] - stdevs[ii] if ii >= set_baseline_periods - 1 else None
        m_two_stdev[ii] = means[ii] - 2 * stdevs[ii] if ii >= set_baseline_periods - 1 else None

        # Track control rules
        out_of_limit_high[ii] = [x + start_period for x, n in enumerate(data[start_period:ii + 1]) if n > ucls[ii]] if ii >= set_baseline_periods - 1 else None
        out_of_limit_low[ii] = [x + start_period for x, n in enumerate(data[start_period:ii + 1]) if n < lcls[ii]] if ii >= set_baseline_periods - 1 else None
        two_of_three_high_2stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 2, 3, 2, 1) if ii >= set_baseline_periods - 1 else None
        two_of_three_low_2stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 2, 3, 2, -1) if ii >= set_baseline_periods - 1 else None
        four_of_five_high_1stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 1, 5, 4, 1) if ii >= set_baseline_periods - 1 else None
        four_of_five_low_1stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 1, 5, 4, -1) if ii >= set_baseline_periods - 1 else None
        seven_high[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 0, 7, 7, 1) if ii >= set_baseline_periods - 1 else None
        seven_low[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 0, 7, 7, -1) if ii >= set_baseline_periods - 1 else None
        seven_trend_high[ii] = qualify_data_sequence(data, max(ii - 7, start_period), ii + 1, 7, increasing) if ii >= set_baseline_periods - 1 else None
        seven_trend_low[ii] = qualify_data_sequence(data, max(ii - 7, start_period), ii + 1, 7, decreasing) if ii >= set_baseline_periods - 1 else None
        eight_out_of_1stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 1, 8, 8, 0) if ii >= set_baseline_periods - 1 else None
        fifteen_within_1stdev[ii] = n_of_x_outside_mean_and_stdev(data, start_period, ii, means[ii], stdevs[ii], 0, 15, 15, 0, False) if ii >= set_baseline_periods - 1 else None
        fourteen_alternate[ii] = qualify_data_sequence(data, max(ii - 7, start_period), ii + 1, 14, alternating_positivity) if ii >= set_baseline_periods - 1 else None


        triggering_points = list_from_lists([
            out_of_limit_high[ii],
            out_of_limit_low[ii],
            two_of_three_high_2stdev[ii],
            two_of_three_low_2stdev[ii],
            four_of_five_high_1stdev[ii],
            four_of_five_low_1stdev[ii],
            seven_high[ii],
            seven_low[ii],
            seven_trend_high[ii],
            seven_trend_low[ii],
            eight_out_of_1stdev[ii],
            fifteen_within_1stdev[ii],
            fourteen_alternate[ii]
        ])

        out_of_control_triggering_points[ii] = triggering_points
        out_of_control[ii] = len(out_of_control_triggering_points[ii]) > 0 if ii >= set_baseline_periods - 1 else None

        # out_of_limit_high[ii] = len([x for x in data[start_period:ii + 1] if x > ucls[ii]]) > 0 if ii > set_baseline_periods else None
        # out_of_limit_low[ii] = len([x for x in data[start_period:ii + 1] if x < lcls[ii]]) > 0 if ii > set_baseline_periods else None
        # two_of_three_high_2stdev[ii] = len([x for x in data[max(ii - 3, start_period):ii + 1] if x > (means[ii] + 2 * stdevs[ii])]) >= 2 if ii > set_baseline_periods else None
        # two_of_three_low_2stdev[ii] = len([x for x in data[max(ii - 3, start_period):ii + 1] if x < (means[ii] - 2 * stdevs[ii])]) >= 2 if ii > set_baseline_periods else None
        # four_of_five_high_1stdev[ii] = len([x for x in data[max(ii - 5, start_period):ii + 1] if x > (means[ii] + stdevs[ii])]) >= 4 if ii > set_baseline_periods else None
        # four_of_five_low_1stdev[ii] = len([x for x in data[max(ii - 5, start_period):ii + 1] if x < (means[ii] - stdevs[ii])]) >= 4 if ii > set_baseline_periods else None
        # seven_high[ii] = len([x for x in data[max(ii - 7, start_period):ii + 1] if x > means[ii]]) == 7 if ii > set_baseline_periods else None
        # seven_low[ii] = len([x for x in data[max(ii - 7, start_period):ii + 1] if x < means[ii]]) == 7 if ii > set_baseline_periods else None
        # seven_trend_high[ii] = strictly_increasing(data[max(ii - 7, start_period):ii + 1]) if ii > set_baseline_periods else None
        # seven_trend_low[ii] = strictly_decreasing(data[max(ii - 7, start_period):ii + 1]) if ii > set_baseline_periods else None
        # eight_out_of_1stdev[ii] = len([x for x in data[max(ii - 8, start_period):ii + 1] if x < means[ii] - stdevs[ii] or x > means[ii] + stdevs[ii]]) == 8 if ii > set_baseline_periods else None
        # fifteen_within_1stdev[ii] = len([x for x in data[max(ii - 15, start_period):ii + 1] if x < means[ii] + stdevs[ii] and x > means[ii] - stdevs[ii]]) == 15 if ii > set_baseline_periods else None
        # fourteen_alternate[ii] = alternating([x for x in list(deltas.values())[max(ii - 14, start_period):ii + 1] if x]) if ii > set_baseline_periods else None


    # format and return
    data = [{'index': x,
             'data_point': data[x],
             'delta': deltas[x],
             'mean': means[x],
             'stdev': stdevs[x],
             'median': medians[x],
             'lcl': lcls[x],
             'm_two_stdev': m_two_stdev[x],
             'm_one_stdev': m_one_stdev[x],
             'p_one_stdev': p_one_stdev[x],
             'p_two_stdev': p_two_stdev[x],
             'ucl': ucls[x],
             'out_of_limit_high': out_of_limit_high[x],
             'out_of_limit_low': out_of_limit_low[x],
             'two_of_three_high_2stdev': two_of_three_high_2stdev[x],
             'two_of_three_low_2stdev': two_of_three_low_2stdev[x],
             'four_of_five_high_1stdev': four_of_five_high_1stdev[x],
             'four_of_five_low_1stdev': four_of_five_low_1stdev[x],
             'seven_high': seven_high[x],
             'seven_low': seven_low[x],
             'seven_trend_high': seven_trend_high[x],
             'seven_trend_low': seven_trend_low[x],
             'eight_out_of_1stdev': eight_out_of_1stdev[x],
             'fifteen_within_1stdev': fifteen_within_1stdev[x],
             'fourteen_alternate': fourteen_alternate[x],
             'out_of_control_triggering_points': out_of_control_triggering_points[x],
             'out_of_control': out_of_control[x]} for x in range(len(data))]
    return data

def control_data_and_deltas(data: List[Union[int, float]],
                            set_baseline_periods: int = None,
                            trailing_window: int = None
                            ) -> List[Dict[str, Any]]:
    """
    Calculates the control of both raw data and the deltas of that data to check for overall control

    :param data: raw data to be analyzed
    :param: set_baseline_periods: The number of periods that must pass before evaluating the statistics
    :param: trailing_window: The amount of past periods to evaluate for control (should be at least 15 since control includes
     checks of at least past 15 periods
    :return: List Dict of values by period
    """
    # gather control of raw data
    controlled_data = control(data, set_baseline_periods, trailing_window)

    # gather control of deltas
    deltas = [x['delta'] for x in controlled_data][1:]
    controlled_deltas = control(deltas, set_baseline_periods, trailing_window)
    controlled_deltas.insert(0, {x: None for x in controlled_deltas[0].keys()})

    # merge and return
    ret = []
    for ii in range(len(controlled_data)):
        controlled_deltas[ii] = {f'delta_{key}': value for key, value in controlled_deltas[ii].items()}
        ret.append({**controlled_data[ii], **controlled_deltas[ii]})

    return ret



if __name__ == "__main__":
    import random as rnd
    import pandas as pd
    import cooptools.pandasHelpers as ph
    data = [rnd.normalvariate(100, 25) for ii in range(250)]
    # cc = pd.DataFrame(control_data_and_deltas(data))

    cc = pd.DataFrame(control(data))
    ph.pretty_print_dataframe(cc)





