import datetime
from cooptools.typevalidation import date_tryParse, datestamp_tryParse
from cooptools.coopEnum import CoopEnum
from typing import List
from cooptools.common import verify
from dateutil.relativedelta import relativedelta

class DateIncrementType(CoopEnum):
    SECOND = relativedelta(seconds=1)
    MINUTE = relativedelta(minutes=1)
    HOUR = relativedelta(hours=1)
    DAY = relativedelta(days=1)
    MONTH = relativedelta(months=1)
    YEAR = relativedelta(years=1)

def last_day_of_month(any_day: datetime.date):
    any_day = date_tryParse(any_day)

    # this will never fail
    # get close to the end of the month for any day, and add 4 days 'over'
    next_month_first_day = (any_day.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    # subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
    return next_month_first_day - datetime.timedelta(days=1)


def month_range(start_date, end_date) -> List[datetime.date]:
    date1 = date_tryParse(start_date).replace(day=1)
    date2 = last_day_of_month(date_tryParse(end_date))

    if date2 < date1:
        raise ValueError(f"invalid date range {start_date}->{end_date}")

    months = []
    while date1 < date2:
        month = date1.month
        year = date1.year
        months.append(last_day_of_month(date1))
        next_month = month + 1 if month != 12 else 1
        next_year = year + 1 if next_month == 1 else year
        date1 = date1.replace(month=next_month, year=next_year)

    return months

def increment_between(d1: datetime.datetime | datetime.date,
                      d2: datetime.datetime | datetime.date,
                      increment_type: DateIncrementType):

    if increment_type == DateIncrementType.MONTH:
        return (d2.year - d1.year) * 12 + d2.month - d1.month
    if increment_type == DateIncrementType.DAY:
        return (d2 - d1).days
    if increment_type == DateIncrementType.YEAR:
        return ((d2.year - d1.year) * 12 + d2.month - d1.month) / 12

    raise NotImplementedError(f"increment type {increment_type} has not been implemented for between")

def datetime_add(start_date: datetime.datetime, increment_type: DateIncrementType, increments: int):
    if increment_type == DateIncrementType.DAY:
        return start_date + relativedelta(days=increments)
    if increment_type == DateIncrementType.MONTH:
        return start_date + relativedelta(months=increments)
    if increment_type == DateIncrementType.YEAR:
        return start_date + relativedelta(years=increments)
    if increment_type == DateIncrementType.MINUTE:
        return start_date + relativedelta(minutes=increments)

    raise NotImplementedError(f"increment type {increment_type} has not been implemented for datetime_add")

def datetime_generator(start_date_time, end_date_time, increment_type: DateIncrementType = DateIncrementType.DAY):
    date1 = bucket_datestamp([datestamp_tryParse(start_date_time)], increment_type)[0]
    date2 = bucket_datestamp([datestamp_tryParse(end_date_time)], increment_type)[0]

    verify(lambda: date1 < date2, msg=f"invalid date range {date1}->{date2}", block=True)

    ret = []

    while date1 <= date2:
        yield date1
        date1 += increment_type.value

    return ret


def datetime_range(start_date_time, end_date_time, increment_type: DateIncrementType):
    return list(
        datetime_generator(
            start_date_time,
            end_date_time,
            increment_type
        )
    )

def date_to_condensed_string(date) -> str:
    date = date_tryParse(date)

    mo = str(date.month)
    if len(mo) == 1: mo = f"0{mo}"
    day = str(date.day)
    if len(day) == 1: day = f"0{day}"

    return f"{date.year}{mo}{day}"

def bucket_datestamp(date_stamps: List[datetime.datetime], grouping_method: DateIncrementType = None):
    grouper_switch = {
        DateIncrementType.SECOND: lambda x: x.replace(microsecond=0) if x is not None else None,
        DateIncrementType.MINUTE: lambda x: x.replace(second=0, microsecond=0) if x is not None else None,
        DateIncrementType.HOUR: lambda x: x.replace(minute=0, second=0, microsecond=0) if x is not None else None,
        DateIncrementType.DAY: lambda x: x.replace(hour=0, minute=0, second=0, microsecond=0) if x is not None else None,
        DateIncrementType.MONTH: lambda x: x.replace(day=1, hour=0, minute=0, second=0, microsecond=0) if x is not None else None,
        DateIncrementType.YEAR: lambda x: x.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0) if x is not None else None,
        None: lambda x: x
    }

    return [grouper_switch[grouping_method](datestamp_tryParse(x)) for x in date_stamps]

def yesterday(
        remove_hrs: bool = False,
        remove_min: bool = False,
        remove_sec: bool = False,
        remove_ms: bool = False):
    return datestamp_tryParse(datetime.datetime.today() - datetime.timedelta(days=1),
                              remove_hrs=remove_hrs,
                              remove_min=remove_min,
                              remove_sec=remove_sec,
                              remove_ms=remove_ms)

def today(
        remove_hrs: bool = False,
        remove_min: bool = False,
        remove_sec: bool = False,
        remove_ms: bool = False):
    return datestamp_tryParse(datetime.datetime.today(),
                              remove_hrs=remove_hrs,
                              remove_min=remove_min,
                              remove_sec=remove_sec,
                              remove_ms=remove_ms)

def now(
        remove_hrs: bool = False,
        remove_min: bool = False,
        remove_sec: bool = False,
        remove_ms: bool = False
):
    return datestamp_tryParse(datetime.datetime.now(),
                              remove_hrs=remove_hrs,
                              remove_min=remove_min,
                              remove_sec=remove_sec,
                              remove_ms=remove_ms)

def tomorrow(
        remove_hrs: bool = False,
        remove_min: bool = False,
        remove_sec: bool = False,
        remove_ms: bool = False
):
    return datestamp_tryParse(datetime.datetime.today() + datetime.timedelta(days=1),
                              remove_hrs=remove_hrs,
                              remove_min=remove_min,
                              remove_sec=remove_sec,
                              remove_ms=remove_ms)

if __name__ == "__main__":
    # print(bucket_datestamp([datetime.datetime.now()], grouping_method=DateIncrementType.SECOND))
    # print(bucket_datestamp(['x'], grouping_method=DateIncrementType.YEAR))
    # print(bucket_datestamp([datetime.datetime.now()], grouping_method=None))

    from pprint import pprint
    start = '1/1/23 5:00'
    end = '1/2/23'

    pprint(datetime_range(start_date_time=start, end_date_time=end, increment_type=DateIncrementType.DAY))