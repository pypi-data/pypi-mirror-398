from cooptools.plotting import plot_series
import cooptools.statistics.controlChart.controlChart as cc
import matplotlib.pyplot as plt
from typing import List

def animate_control(data, ax, trailing_window=None, x_s: List = None):
    control = cc.control_data_and_deltas([float(x) for x in data], trailing_window=trailing_window)
    ax.clear()
    plot_control_chart(control, ax, trailing_window, x_s=x_s)


def plot_show_and_save(control_data, trailing_window: int, show: bool = True, x_s: List = None, out_dirs: List = None):
    f, axes = plt.subplots(1, 1, figsize=(15, 10))
    plot_control_chart(control_data, axes, trailing_window=trailing_window, x_s=x_s)

    if show:
        plt.show()

    if out_dirs is not None:
        for dir in out_dirs:
            f.savefig(dir)


def plot_control_chart(control, ax, trailing_window=None, x_s: List = None):
    if control is None or ax is None:
        return

    shade_ooc(control, ax, x_s=x_s)
    plot_lcl_trend(control, ax, x_s=x_s)
    plot_mean_trend(control, ax, x_s=x_s)
    plot_ucl_trend(control, ax, x_s=x_s)
    plot_ucl(control, ax, trailing_window, x_s=x_s)
    plot_p_one_stdev(control, ax, trailing_window, x_s=x_s)
    plot_p_two_stdev(control, ax, trailing_window, x_s=x_s)
    plot_m_one_stdev(control, ax, trailing_window, x_s=x_s)
    plot_m_two_stdev(control, ax, trailing_window, x_s=x_s)
    plot_lcl(control, ax, trailing_window, x_s=x_s)
    plot_mean(control, ax, trailing_window, x_s=x_s)
    plot_data(control, ax, x_s=x_s)
    plot_out_of_controls(control, ax, x_s=x_s)
    plot_outliers(control, ax, x_s=x_s)


def shade_ooc(control, ax, x_s: List = None):
    ax.fill_between(x_s if x_s else range(len(control)),
                    min([x['data_point'] for x in control] + [x['lcl'] for x in control if x['lcl']]),
                    max([x['data_point'] for x in control] + [x['ucl'] for x in control if x['ucl']]),
                    where=([x['out_of_control'] or control[min(len(control) - 1, ii + 1)]['out_of_control'] for ii, x in
                            enumerate(control)]),
                    alpha=0.25)


def plot_line(control, ax, key, color, x_s: List = None, trailing_window=None, last_only: bool = False, line_style='--',
              line_width=2):
    if last_only:
        data = [(x_s[ind] if x_s else ind, control[-1][key]) for ind, x in enumerate(control) if
                x[key] is not None and ind > len(control) - trailing_window]
    else:
        data = [(x_s[ind] if x_s else ind, x[key]) for ind, x in enumerate(control) if x[key] is not None]
    plot_series(data, ax, color=color, line_style=line_style, line_width=line_width)


def plot_ucl(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='ucl',
              color='r',
              line_style='--',
              line_width=2)


def plot_p_one_stdev(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='p_one_stdev',
              color='grey',
              line_style='--',
              line_width=1)


def plot_p_two_stdev(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='p_two_stdev',
              color='grey',
              line_style='--',
              line_width=1)


def plot_m_one_stdev(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='m_one_stdev',
              color='grey',
              line_style='--',
              line_width=1)


def plot_m_two_stdev(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='m_two_stdev',
              color='grey',
              line_style='--',
              line_width=1)


def plot_lcl(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='lcl',
              color='r',
              line_style='--',
              line_width=2)


def plot_ucl_trend(control, ax, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              last_only=False,
              key='ucl',
              color='r',
              line_style='--',
              line_width=1)


def plot_lcl_trend(control, ax, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              last_only=False,
              key='lcl',
              color='r',
              line_style='--',
              line_width=1)


def plot_mean(control, ax, trailing_window, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              trailing_window=trailing_window,
              last_only=True,
              key='mean',
              color='g',
              line_style='--',
              line_width=2)


def plot_mean_trend(control, ax, x_s: List = None):
    plot_line(control,
              ax,
              x_s=x_s,
              last_only=False,
              key='mean',
              color='g',
              line_style='--',
              line_width=1)


def plot_data(control, ax, x_s: List = None):
    data = [(x_s[ind] if x_s else ind, x['data_point']) for ind, x in enumerate(control) if x['data_point'] is not None]
    plot_series(data, ax, color='grey', series_type='scatter', point_size=2)


def list_from_lists(lists_of_lists: List[List]):
    the_set = set()

    for alist in lists_of_lists:
        if alist is not None:
            try:
                the_set.update(list_from_lists(alist))
            except Exception as e:
                the_set.update(alist)
    return list(the_set)


def plot_out_of_controls(control, ax, x_s: List = None):
    triggering_indexes = list_from_lists(
        [x['out_of_control_triggering_points'] for x in control if x['out_of_control_triggering_points']])
    oocs = [(x_s[ind] if x_s else ind, control[ind]['data_point']) for ind in triggering_indexes]
    plot_series(oocs, ax, color='y', series_type='scatter', point_size=6)


def plot_outliers(control, ax, x_s: List = None):
    outliers = set()
    for ii, x in enumerate(control):
        if x['out_of_limit_high']:
            outliers.update([(x_s[ind] if x_s else ind, control[ind]['data_point']) for ind in x['out_of_limit_high']])
        if x['out_of_limit_low']:
            outliers.update([(x_s[ind] if x_s else ind, control[ind]['data_point']) for ind in x['out_of_limit_low']])

    if len(outliers) > 0:
        plot_series(list(outliers), ax, color='r', series_type='scatter')


if __name__ == "__main__":
    import random as rnd
    import pandas as pd
    import cooptools.pandasHelpers as ph

    data = [rnd.normalvariate(100, 25) for ii in range(250)]
    # cc = pd.DataFrame(control_data_and_deltas(data))
    trailing_window = 100
    control_data = cc.control(data, trailing_window=trailing_window)
    cc_df = pd.DataFrame(control_data)
    ph.pretty_print_dataframe(cc_df)

    f, axes = plt.subplots(1, 1, figsize=(15, 10))
    plot_control_chart(control_data, axes, trailing_window=trailing_window)
    plt.show()
