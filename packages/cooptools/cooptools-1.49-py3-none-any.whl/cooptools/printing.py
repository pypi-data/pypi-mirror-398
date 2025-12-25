import pandas as pd
from typing import List, Tuple
import numpy as np


def pretty_print_dataframe(df: pd.DataFrame, title: str = None):
    pretty_format_dataframe(df, title)

def pretty_format_dataframe(df: pd.DataFrame, title: str = None):
    ret = ""

    if title:
        ret += title

    with pd.option_context('display.max_rows', 500, 'display.max_columns', 2000, 'display.width', 250):
        ret += f"{df}\n"

    return ret


def pretty_print_list_of_list(lst_of_lst: List[List], title: str = None):
    print(pretty_format_list_of_list(lst_of_lst, title))

def pretty_format_list_of_list(lst_of_lst: List[List], title: str = None):
    ret = ""

    if title:
        ret += title

    n = np.array([[len(str(x)) for x in l] for l in lst_of_lst])
    maxxs = np.amax(n, axis=0)
    # Print the rows
    for row in lst_of_lst:
        joined = ''.join(str(x).ljust(maxxs[ii] + 2) for ii, x in enumerate(row))
        ret += f"\n\t{joined}"

    return ret

def pretty_format_list_of_tuple(lst_of_tup: List[Tuple], title: str = None):
    ret = ""

    if title:
        ret += title

    n = np.array([[len(str(x)) for x in l] for l in lst_of_tup])
    maxxs = np.amax(n, axis=0)
    # Print the rows
    for row in lst_of_tup:
        joined = ''.join(str(x).ljust(maxxs[ii] + 2) for ii, x in enumerate(row))
        ret += f"\n\t{joined}"

    return ret