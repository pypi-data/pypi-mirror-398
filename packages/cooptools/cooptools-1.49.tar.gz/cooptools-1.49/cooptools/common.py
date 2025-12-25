import math
import uuid
from typing import List, Union, Tuple, Iterable, Callable, Sequence, Protocol, TypeVar, Dict
import itertools
import struct
import imghdr
import numpy as np
import bisect
import string
import logging
from dataclasses import dataclass
import statistics
from cooptools.protocols import ComparableProtocol
import re
from functools import lru_cache

logger = logging.getLogger(__name__)

LETTERS = string.ascii_lowercase
NUMBERS = '1234567890'
CHARS = '!@#$%^&*()-_=+[{]};:"/?.>,<`~'

def flattened_list_of_lists(list_of_lists: Iterable[Iterable], unique: bool = False) -> List:
    flat = list(itertools.chain.from_iterable(list_of_lists))

    if unique:
        flat = list(set(flat))

    return flat

def all_indxs_in_lst(lst: List, value) -> List[int]:
    idxs = []
    idx = -1
    while True:
        try:
            idx = lst.index(value, idx + 1)
            idxs.append(idx)
        except ValueError as e:
            break
    return idxs

def is_non_string_iterable(x):
    if type(x) in [str]:
        return False

    try:
        some_object_iterator = iter(x)
        return True
    except TypeError as te:
        return False

def next_perfect_square_rt(n: int) -> int:
    int_root_n = int(math.sqrt(n))
    if int_root_n == n:
        return n
    return int_root_n + 1

def try_resolve_guid(id: str) -> Union[str, uuid.UUID]:

    try:
        return uuid.UUID(id)
    except:
        return id

def split_strip(txt: str):
    return [x.strip() for x in txt.split(',')]

def duplicates_in_list(lst: Iterable) -> List:
    _lst = [frozenset(x) if is_non_string_iterable(x) else x for x in lst]
    counts = [_lst.count(x) for x in _lst]

    ret = list(set([_lst[ii] for ii, x in enumerate(counts) if x > 1]))

    return ret


def verify(verify_func: Callable, msg: str=None, msg_sub: str=None, block: bool=True):
    if msg_sub is not None:
        msg += f"\n\t{msg_sub}"

    result = verify_func()

    if not result and block:
        raise ValueError(msg)
    elif not result:
        logger.debug(msg)

    return result


def bound_value(val: ComparableProtocol,
               gte: ComparableProtocol = None,
               lte: ComparableProtocol = None):
    ret = val
    if gte is not None and ret < gte:
        ret = gte
    elif lte is not None and ret > lte:
        ret = lte
    return ret

def verify_val(val: ComparableProtocol,
               gt: ComparableProtocol = None,
               gte: ComparableProtocol = None,
               lt: ComparableProtocol = None,
               lte: ComparableProtocol = None,
               eq: ComparableProtocol = None,
               not_none: bool = False,
               error_msg: str = None,
               block: bool = True) -> bool:
    if eq is not None:
        eq_tst = lambda: val == eq
        eq_txt = f"{eq} == {val}"
    else:
        eq_tst = lambda: True
        eq_txt = f""

    if gte is not None:
        low_tst = lambda: val >= gte
        low_txt = f"{gte} <="
    elif gt is not None:
        low_tst = lambda: val > gt
        low_txt = f"{gt} <"
    else:
        low_tst = lambda: True
        low_txt = f""

    if lte is not None:
        hi_tst = lambda: val <= lte
        hi_txt = f"<= {lte}"
    elif lt is not None:
        hi_tst = lambda: val < lt
        hi_txt = f"< {lt}"
    else:
        hi_tst = lambda: True
        hi_txt = ""

    if not_none:
        not_none_tst = lambda : val is not None
        not_none_txt = f"[not None]"
    else:
        not_none_tst = lambda: True
        not_none_txt = f""

    tst = lambda: low_tst() and hi_tst() and eq_tst() and not_none_tst()

    msg = f"invalid value: {eq_txt}{low_txt} {val} {hi_txt} {not_none_txt} is not valid"
    return verify(tst, msg, msg_sub=error_msg, block=block)


def verify_unique(lst: Iterable, error_msg: str = None):
    dups = duplicates_in_list(lst)

    tst = lambda: len(dups) == 0
    msg = f"All the values are not unique. Dups: {dups}"
    verify(tst, msg, error_msg)

def verify_len_match(iterable1,
                     iterable2,
                     error_msg: str = None,
                     block:bool = True):
    msg = f"{iterable1} and {iterable2} do not have the same length ({len(iterable1)} vs {len(iterable2)})"

    tst = lambda: len(iterable1) == len(iterable2)
    verify(tst, msg, error_msg, block=block)

def verify_len(iterable, length: int, error_msg: str = None):
    msg = f"{iterable} does not have len {length} ({len(iterable)})"

    tst = lambda: len(iterable) == length
    verify(tst, msg, error_msg)

def degree_to_rads(degrees: float) -> float:
    return degrees * math.pi / 180

def rads_to_degrees(rads: float) -> float:
    return rads * 180 / math.pi


def bounding_box_of_points(pts: Sequence[Tuple[float, float]]) -> Tuple[float, float, float, float]:
    min_x = min([p[0] for p in pts])
    max_x = max([p[0] for p in pts])
    min_y = min([p[1] for p in pts])
    max_y = max([p[1] for p in pts])

    w = max_x - min_x
    h = max_y - min_y

    return (min_x, min_y, w, h)

def divided_length(inc: float,
                   start: float = None,
                   start_inc: float = None,
                   stop: float = None,
                   stop_inc: float = None,
                   force_to_ends: bool = False) -> List[float]:
    vals = []

    s = start or start_inc
    e = stop or stop_inc

    if s <= e:
        tst = lambda val: verify_val(val, low=start, low_inc=start_inc, hi=stop, hi_inc=stop_inc, block=False)
    else:
        tst = lambda val: verify_val(val, low=stop, low_inc=stop_inc, hi=start, hi_inc=start_inc, block=False)
        inc *= -1

    ii = s
    while tst(ii):
        vals.append(ii)
        ii += inc

    # force to ends
    if force_to_ends:
        remaining_delta = abs(e - vals[-1])
        vals = [x + remaining_delta / (len(vals) - 1) * (ii) for ii, x in enumerate(vals)]

    return vals

def property_name(prop:str):
    return prop.split('=')[0].replace('self.', '').replace('cls.', '')

def get_image_size(fname):
    '''Determine the image type of fhandle and return its size.
    from draco'''
    with open(fname, 'rb') as fhandle:
        head = fhandle.read(24)
        if len(head) != 24:
            return
        if imghdr.what(fname) == 'png':
            check = struct.unpack('>i', head[4:8])[0]
            if check != 0x0d0a1a0a:
                return
            width, height = struct.unpack('>ii', head[16:24])
        elif imghdr.what(fname) == 'gif':
            width, height = struct.unpack('<HH', head[6:10])
        elif imghdr.what(fname) == 'jpeg':
            try:
                fhandle.seek(0)  # Read 0xff next
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf:
                    fhandle.seek(size, 1)
                    byte = fhandle.read(1)
                    while ord(byte) == 0xff:
                        byte = fhandle.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', fhandle.read(2))[0] - 2
                # We are at a SOFn block
                fhandle.seek(1, 1)  # Skip `precision' byte.
                height, width = struct.unpack('>HH', fhandle.read(4))
            except Exception:  # IGNORE:W0703
                return
        else:
            return
        return width, height

# https://stackoverflow.com/questions/43099542/python-easy-way-to-do-geometric-mean-in-python
def geo_mean(iterable: Iterable):
    a = np.array([1 + x for x in iterable if x not in [None, np.nan]])

    ret = a.prod() ** (1.0 / len(a))

    if ret == np.inf or ret == np.nan:
        ret = np.exp(np.log(a).mean())

    return float(ret - 1)

def from_schema(schema, **kwargs):
    definition = schema.__dict__
    for kwarg, val in kwargs.items():
        definition[kwarg] = val

    return type(schema)(**definition)

def insert_sorted_list(list, n):
    bisect.insort(list, n)
    return list

def cross_apply(items: Iterable[Iterable]) -> Iterable[Tuple]:
    return [x for x in itertools.product(*items)]

def all_equal(iterator):
    iterator = iter(iterator)
    try:
        first = next(iterator)
    except StopIteration:
        return True
    return all(first == x for x in iterator)

def chunks(lst: Iterable, n: int):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

U = TypeVar('U')


def filter(
        options: Iterable[U],
        qualifier: Callable[[U], bool] = None
) -> List[U]:
    if qualifier is None:
        return options

    ret = [
        x for x in options if qualifier(x)
    ]
    return ret


def replace_many_in_str(raw: str, replacements: Dict[str, str]) -> str:
    ret = raw
    for k, v in replacements.items():
        ret.replace(k, v)
    return ret


def lst_tuples_from_lst(lst: Iterable) -> List:
    old = None
    ret = []

    for i in lst:
        if old is not None:
            ret.append((old, i))
        old = i
    return ret


def case_insensitive_replace(text, old_substring, new_substring):
    """
    Checks if a string contains a substring (case-insensitively) and replaces all occurrences.

    Args:
        text: The main string to search within.
        old_substring: The substring to search for.
        new_substring: The substring to replace with.

    Returns:
        The modified string with replacements, or the original string if the substring is not found.
    """

    regex = re.compile(re.escape(old_substring), re.IGNORECASE)
    return regex.sub(new_substring, text)


@dataclass(frozen=True, slots=True)
class NumericalDescription:
    vals: List[float | int]

    def __post_init__(self):
        object.__setattr__(self, 'vals', [float(x) for x in self.vals])

    @property
    def Sum(self):
        return sum(self.vals)

    @property
    def Count(self):
        return len(self.vals)

    @property
    def Min(self):
        return min(self.vals)

    @property
    def Max(self):
        return max(self.vals)

    @property
    def Average(self):
        return self.Sum / self.Count

    @property
    def Median(self):
        return statistics.median(self.vals)

def json_serializable_dict(dic: Dict):
    ret = {}
    for k, v in dic.items():
        if type(v) == dict:
            ret[str(k)] = json_serializable_dict(v)
        else:
            ret[str(k)] = str(v)
    return ret

@lru_cache()
def int_to_letter(val: int):
    ret = ""

    verify_val(val=val, gte=0)
    curr = val
    while True:
        div = curr // 26
        mod = curr % 26

        ret += LETTERS[mod]
        curr = div

        if div == 0:
            break

        # if curr < 26:
        #     ret += LETTERS[curr]
        #     break
        #
        # add = min(curr // 26, 26)
        #
        # if 26 >= add > 0:
        #     ret += LETTERS[add - 1]
        #
        # curr = curr / add

        # if add >= 26:
        #     ret += LETTERS[25]
        # else:
        #     ret += LETTERS[add]

    return ret


if __name__ == "__main__":
    # print(bucket_datestamp([datetime.datetime.now()], grouping_method=DateGroupingType.YEAR))
    pass

    items = [
        ['a', 'b', 'c'],
        [1, 2],
        ["hello", "fresh"]
    ]
    print(cross_apply(items))

    def test_int_to_letter():
        # assert int_to_letter(30) == 'ae'
        print(int_to_letter(30004))


    test_int_to_letter()