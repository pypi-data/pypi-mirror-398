from typing import Dict, Any, Tuple
import numpy.random as nrnd
import datetime
import random as rnd
from cooptools.common import LETTERS, NUMBERS, CHARS

def weighted_random_choice(choices_dict: Dict[Any, float], seed: int = None):
    if seed is not None:
        rnd.seed(seed)

    total = sum([v for k, v in choices_dict.items()])
    selection_probs = [v / total for k, v in choices_dict.items()]

    return list(choices_dict)[nrnd.choice(len(choices_dict), p=selection_probs)]

def random_datetime(date: datetime.date = None,
                    relevant_days_past: int = None,
                    start_date: datetime.datetime = None,
                    end_date: datetime.datetime = None):

    if relevant_days_past is None:
        relevant_days_past = 90

    if start_date and end_date is not None and end_date > start_date:
        delta_days = rnd.randint(0, (end_date - start_date).days)
        date = start_date + datetime.timedelta(days=delta_days)
        days = 0
    elif date is None:
        date = datetime.datetime.now().replace(hour=0, microsecond=0, second=0)
        days = rnd.randint(-relevant_days_past, 0)
    else:
        days = 0

    hrs = rnd.randint(0, 23)
    seconds = rnd.randint(0, 59)

    return date + datetime.timedelta(days=days, hours=hrs, seconds=seconds)

def a_string(k: int = None, include_alpha: bool = True, include_numeric: bool = False, include_chars: bool = False):
    if k is None:
        k = rnd.randint(3, 10)

    options = ''

    if not any([include_alpha, include_numeric, include_chars]):
        raise ValueError(f"At least one of [include_alpha, include_numeric, include_chars] must be True")

    if include_alpha:
        options += LETTERS

    if include_numeric:
        options += NUMBERS

    if include_chars:
        options += CHARS

    return ''.join(rnd.choices(options, k=k))

def a_phrase(words: int = None, include_alpha: bool = True, include_numeric: bool = False, include_chars: bool = False):
    if words is None:
        words = rnd.randint(3, 10)
    return ' '.join([
        a_string(rnd.randint(3, 10),
                 include_alpha=include_alpha,
                 include_numeric=include_numeric,
                 include_chars=include_chars) for x in range(words)
    ])

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    choices = {
        "a": 1,
        "b": 2,
        "c": 1.5,
        "d": 4
    }

    #TEST 1
    # rnd.seed(0)
    # ret = weighted_random_choice(choices)
    # print(ret)

    #TEST 2
    # rets = {}
    # for ii in range(0, 1000):
    #     ret = weighted_random_choice(choices)
    #     rets.setdefault(ret, 0)
    #     rets[ret] += 1
    #
    # for k, v in choices.items():
    #     print(f"{k} -- {v} ({round(v / sum([x for x in choices.values()]) * 100, 1)}%)")
    #
    # for k, v in rets.items():
    #     print(f"{k} -- {v} ({round(v / sum([x for x in rets.values()]) * 100, 1)}%)")


    # TEST 3 - verify strings and pharase
    for i in range(10):
        print(a_string(include_alpha=False, include_numeric=True, include_chars=False))

    for i in range(5):
        print(a_phrase())
