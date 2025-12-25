import dateutil.parser
from datetime import date, datetime, timezone as tz
# import pandas as pd
import uuid
import math
import logging
import numpy as np

def float_as_currency(val: float) -> str:
    return "${:,.2f}".format(round(val, 2))

def float_parse(value) -> float:
    try:
        return float(value)
    except Exception as e:
        raise ValueError(f"Unable to parse value: {value} as a float") from e


def int_tryParse(value) -> int:
    try:
        return int(value)
    except:
        return None


def date_tryParse(value, allow_none: bool = True) -> date:
    ret = force_to_date_or_None(value)
    if not allow_none and ret is None:
        raise ValueError(f"value cannot be None")

    return ret


def datestamp_tryParse(value,
                       remove_month: bool = False,
                       remove_day: bool = False,
                       remove_hrs: bool = False,
                       remove_min: bool = False,
                       remove_sec: bool = False,
                       remove_ms: bool = False,
                       include_time: bool = True,
                       allow_none: bool = True) -> datetime:
    val = force_to_datetime_or_None(value)

    if val is None and not allow_none:
        raise ValueError(f"value cannot be None")

    if val is None:
        return val

    if not include_time:
        remove_min = True
        remove_hrs = True
        remove_sec = True
        remove_ms = True

    if remove_month:
        val.replace(month=0)

    if remove_day:
        val.replace(day=0)

    if remove_hrs:
        val.replace(hour=0)

    if remove_min:
        val.replace(minute=0)

    if remove_sec:
        val.replace(second=0)

    if remove_ms:
        val = val.replace(microsecond=0)

    return val

def uuid_tryparse(val) -> uuid.UUID:
    if isinstance(val, uuid.UUID):
        return val
    elif isinstance(val, str) and val != '':
        return uuid.UUID(val)
    elif isinstance(val, float) and math.isnan(val):
        return None
    else:
        raise TypeError(f"Unhandled UUID value: {val}")

def force_to_date_or_None(val):
    my_datetime = force_to_datetime_or_None(val)
    if my_datetime is None:
        return None
    else:
        return my_datetime.date()

def force_to_datetime_or_None(val, force_to_midnight: bool = False):
    try:
        # parse supported inputs to a datetime
        if val is None:
            return val
        elif isinstance(val, datetime):
            ret = val
        elif isinstance(val, date):
            ret = datetime.combine(val, datetime.min.time())
        # elif isinstance(val, pd.Timestamp):
        #     the_date = val.to_pydatetime().date()
        #     ret = datetime.combine(the_date, datetime.min.time())
        elif isinstance(val, np.datetime64):
            ts = (val - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 's')
            ret = datetime.utcfromtimestamp(ts)
        else:
            try:
                val = dateutil.parser.parse(val)
            except dateutil.parser.ParserError as e:
                # attempt a parse of YYYYDDMM format
                val = dateutil.parser.parse(val,
                                            parserinfo=dateutil.parser.parserinfo(
                                                                           yearfirst=True,
                                                                           dayfirst=True
                                                                       ))
            ret = force_to_datetime_or_None(val)

        # force to midnight if requested
        if force_to_midnight:
            ret = datetime.combine(ret.date(), datetime.min.time())

        # return value that was parsed
        return ret
    except Exception as e:
        logging.warning(f"unable to parse val {val} [{type(val)}] as datetime: {e}")
        return None

def bool_tryparse(val: str | int | bool):
    if type(val) == bool:
        return val

    if type(val) == str and val.upper() in ['F', 'FALSE']:
        return False

    if type(val) == int and val == 0:
        return False

    if type(val) == str and val.upper() in ['T', 'TRUE']:
        return True

    if type(val) == int and val == 1:
        return True

    raise ValueError(f"The val: {val} is unrecognized as bool")

if __name__ == "__main__":
    try_vals = [
        date.today(),
        '10.21.21',
        '10/21/21',
        None,
        datetime.today(),
        '2014-08-01 11:00:00+02:00'
    ]

    results = map(force_to_datetime_or_None, try_vals)

    print(list(results))

    results = map(lambda x: datestamp_tryParse(x, include_ms=False, allow_none=False), try_vals)
    print(list(results))