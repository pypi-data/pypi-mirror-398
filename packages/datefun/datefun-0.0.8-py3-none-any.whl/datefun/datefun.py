"""
Operations with ISO string representing date
Methods can detected by prefix:
dt_ prefixed method results iso_date string (empty string means there was problem)

"""

from datetime import datetime, timedelta, date
from typing import Any
from dateutil import easter
from math import floor

def dt_make(year: int, month: int, day: int) -> str:
    """
    If day is too big then try minimize to end of month. All other errors are errors.
    """
    iso_date = f"{year:04}-{month:02}-{day:02}"
    if is_valid_date(iso_date):
        return iso_date
    else:
        # see põhjustab rekursiooni!!!
        #iso_date = dt_make(year, month, 1)
        #if is_valid_date(iso_date):
        #    return dt_month_end(iso_date)
        return ""

def dt_today() -> str:
    obj = datetime.now()
    return dt_from_object(obj)


def is_valid_date(iso_date: str) -> bool:
    """
    Checks if argument is really possible ISO date (YYYY-MM-DD)
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return False
    possible = f"{year:04}-{month:02}-{day:02}"
    try:
        _ = datetime.fromisoformat(possible) # this one can emit exception on wrong input
    except:
        return False
    return True

def dt_validate(iso_date: str) -> str:
    """
    Makes input string to regular ISO date if possible (25-9-6 -> 2025-09-06)
    Empty string as result marks error.
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    return dt_make(year, month, day)


def dt_year_start(iso_date: str) -> str:
    """
    Returns first day of year of input date (2025-09-13 -> 2025-01-01)
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    return dt_make(year, 1, 1)

def dt_year_end(iso_date: str) -> str:
    """
    Returns last day of year of input date (2025-09-13 -> 2025-12-31)
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    return dt_make(year, 12, 31)

def dt_month_start(iso_date: str) -> str:
    """
    Returns first day of month of input date (2025-09-13 -> 2025-09-01)
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    return dt_make(year, month, 1)


def dt_from_object(obj: datetime | date) -> str:
    format = r"%Y-%m-%d"
    return obj.strftime(format)

def int_days_in_month(iso_date: str) -> int:
    """
    Returns number of days in month identified by date
    Solution: take date, find 1st in month (keep), add more then 32 days, find 1st in that month, subtract to find diff in days
    """
    start_of_month = datetime.fromisoformat(dt_month_start(iso_date))
    day_in_next_month = start_of_month + timedelta(days=40)
    start_of_next_month = datetime.fromisoformat(dt_month_start(dt_from_object(day_in_next_month)))
    diff = start_of_next_month - start_of_month
    return diff.days

def dt_month_end(iso_date: str) -> str:
    """
    Returns last day of month of input date (2025-09-13 -> 2025-09-30)
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    day = int_days_in_month(iso_date)
    return dt_make(year, month, day)


def int_weekday(iso_date: str) -> int:
    """
    monday = 1, sunday = 7 # for human
    Probably we should add optional second argument week_start_monday: bool = True and code for False: sunday = 1, saturday = 7
    """
    obj_date = datetime.fromisoformat(iso_date)
    weekday: int = obj_date.weekday() # 0 = monday
    return weekday + 1

def dt_week_start(iso_date: str, week_start_monday: bool = True) -> str:
    """
    Returns first day of week of input date depending whether week starts on monday or sunday
    if week starts on monday: (2025-10-01 -> 2025-09-29)
    else if week starts on sunday: (2025-10-01 -> 2025-09-28)
    """
    year, month, day = trio_date(iso_date)

    if day == 0:
        return ''
    
    obj_date = datetime.fromisoformat(iso_date)

    weekday: int = obj_date.weekday() # 0 = monday

    if not week_start_monday:
        if weekday == 6:
            weekday = 0
        else:
            weekday = weekday + 1

    return dt_add_days(iso_date, -weekday)


def dt_week_end(iso_date: str, week_start_monday: bool = True) -> str:
    """
    Returns last day of week of input date depending whether week starts on monday or sunday
    if week starts on monday: (2025-10-01 -> 2025-10-05)
    else if week starts on sunday: (2025-10-01 -> 2025-10-04)
    """
    return dt_add_days(dt_week_start(iso_date, week_start_monday), 6)


def dt_quarter_start(iso_date: str) -> str:
    """
    Returns first day of quarter of input date (2025-09-13 -> 2025-07-01)
    """
    return _get_dt_quarter(iso_date, True)


def dt_quarter_end(iso_date: str) -> str:
    """
    Returns last day of quarter of input date (2025-09-13 -> 2025-09-30)
    """
    return _get_dt_quarter(iso_date, False)


def _get_dt_quarter(iso_date: str, get_quarter_start: bool) -> str:
    """
    Returns first or last day of quarter of input date depending on get_quarter_start value
    """
    year, month, day = trio_date(iso_date)

    if day == 0:
        return ''
    
    quarter: int = int((month - 1) / 3) + 1

    quarters: dict[int, tuple[str, str]] = {
        1 : (dt_make(year, 1, 1), dt_make(year, 3, 31)),
        2 : (dt_make(year, 4, 1), dt_make(year, 6, 30)),
        3 : (dt_make(year, 7, 1), dt_make(year, 9, 30)),
        4 : (dt_make(year, 10, 1), dt_make(year, 12, 31))
    }

    return quarters[quarter][0 if get_quarter_start else 1]


def dt_semiyear_start(iso_date: str) -> str:
    """
    Returns first day of semiyear of input date (2025-09-13 -> 2025-07-01)
    """
    return _get_dt_semiyear(iso_date, True)


def dt_semiyear_end(iso_date: str) -> str:
    """
    Returns last day of quarter of input date (2025-09-13 -> 2025-12-31)
    """
    return _get_dt_semiyear(iso_date, False)


def _get_dt_semiyear(iso_date: str, get_semiyear_start: bool) -> str:
    """
    Returns first or last day of semiyear of input date depending on get_semiyear_start value
    """
    year, month, day = trio_date(iso_date)

    if day == 0:
        return ''
    
    semiyear: int = int((month - 1) / 6) + 1

    semiyears: dict[int, tuple[str, str]] = {
        1 : (dt_make(year, 1, 1), dt_make(year, 6, 30)),
        2 : (dt_make(year, 7, 1), dt_make(year, 12, 31))
    }

    return semiyears[semiyear][0 if get_semiyear_start else 1]


def is_leap_year(year_or_date: int | str) -> bool:
    if isinstance(year_or_date, int):
        year = year_or_date
    else:
        year, month, day = trio_date(year_or_date)
        if day == 0:
            return False # unclear
    if year % 4 == 0:
        if year % 100 == 0:
            if year % 400 == 0:
                return True
            else:
                return False
        else:
            return True
    else:
        return False

def dt_add_years(iso_date: str, many_years: int, interpret_0228_as_monthend: bool = True) -> str:
    """
    Add full years. If result is 29th february and this is not possible, then return 28th febr
    if flag interpret2802_as_monthend is True then 28th febr becames 29th in leap years
    if False then stays 28th event in leap years
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    go29: bool = False
    if day == 28 and month == 2 and interpret_0228_as_monthend:
        go29 = True
    if day == 29 and month == 2:
        go29 = True
    new_year = year + many_years
    leap_year = is_leap_year(new_year)
    if leap_year and go29:
        new_day = 29
    else:
        new_day = 28
    new_iso_date = dt_make(new_year, month, new_day)
    if not is_valid_date(new_iso_date):
        new_iso_date = dt_make(new_day, month, 28)
    return new_iso_date

def dt_add_months(iso_date: str, many_months: int, stay_in_month_end: bool = True) -> str:
    """
    Add full months. if start and end months have different days in month and start date is end of month try to keep end of month
    """
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    go_end: bool = False
    end_day_1 = int_days_in_month(iso_date)
    if end_day_1 == day and stay_in_month_end:
        go_end = True
    new_month = month + many_months
    new_year = year
    while new_month > 12:
        new_month -= 12
        new_year += 1
    while new_month < 1:
        new_month += 12
        new_year -= 1

    end_day_2 = int_days_in_month(dt_make(new_year, new_month, 1))
    if go_end:
        new_iso_date = dt_make(new_year, new_month, end_day_2)
    else:
        new_day = day
        if new_day > end_day_2:
            new_day = end_day_2
        new_iso_date = dt_make(new_year, new_month, new_day)
    return new_iso_date

def dt_add_days(iso_date: str, many_days: int) -> str:
    year, month, day = trio_date(iso_date)
    if day == 0:
        return ""
    obj_date = datetime.fromisoformat(iso_date)
    new_obj_date = obj_date + timedelta(days=many_days)
    return dt_from_object(new_obj_date)


def dt_easter(year: int) -> str:
    """
    Calculating easter (western) date for a given year using dateutil.easter module
    """
    if not isinstance(year, int):
        return ''
    elif year < 1900:
        return ''

    return dt_from_object(easter.easter(year)) # Method = 3 which is Western


def dt_easter_gauss(year: int) -> str:
    """
    Calculating easter date for a given year using Gauss' Algorithm
    """
    if not isinstance(year, int):
        return ''
    elif year < 1900:
        return ''

    a = year % 19
    b = year % 4
    c = year % 7

    p = floor(year / 100)
    q = floor((13 + 8 * p) / 25)
    m = (15 - q + p - p // 4) % 30
    n = (4 + p - p // 4) % 7
    d = (19 * a + m) % 30
    e = (2 * b + 4 * c + 6 * d + n) % 7

    days = (22 + d + e)
    
    if d == 29 and e == 6:
        return dt_make(year, 4, 19) # Corner case
    elif d == 28 and e == 6:
        return dt_make(year, 4, 18) # Corner case
    elif days > 31:
        return dt_make(year, 4, (days - 31)) # Month is april
    else:
        return dt_make(year, 3, days) # Month is March


def dt_good_friday(year: int) -> str:
    """
    Finding good friday date for a given year from easter date
    """
    return dt_add_days(dt_easter(year), -2)


def dt_pentecost(year: int) -> str:
    """
    Finding pentecost date for a given year from easter date
    """
    return dt_add_days(dt_easter(year), 49)


def dt_add_week(iso_date: str, many_weeks: int) -> str:
    """
    Add full weeks
    """
    if not is_valid_integer(many_weeks):
        return ''
    
    return dt_add_days(iso_date, int(many_weeks) * 7)


def dt_add_quarter(iso_date: str, many_quarters: int, stay_in_month_end: bool = True) -> str:
    """
    Add full quarters. if start and end quarter have different days in month and start date is end of month try to keep end of month
    """
    if not is_valid_integer(many_quarters):
        return ''
    
    return dt_add_months(iso_date, int(many_quarters) * 3, stay_in_month_end)


def dt_add_semiyear(iso_date: str, many_semiyear: int, stay_in_month_end: bool = True) -> str:
    """
    Add full semiyear. if start and end semiyear have different days in month and start date is end of month try to keep end of month
    """
    if not is_valid_integer(many_semiyear):
        return ''
    
    return dt_add_months(iso_date, int(many_semiyear) * 6, stay_in_month_end)

# TODO today, compare (dt1, op, d2) => diff(dt1, dt2) in days / months (full/start) / etc
# TODO interacts (periods)

def trio_date(iso_date: str) -> tuple[int, int, int]:
    """
    Helper method to get 3 parts of date delimited by minus, and return tuple. day=0 marks error
    """
    try:
        [year_str, month_str, day_str] = iso_date.split("-", 3) # this one can emit exception on wrong input
        year = int(year_str)
        month = int(month_str)
        day = int(day_str)
        if month > 0 and day > 0:
            return (year, month, day)
        else:
            return (0, 0, 0)
    except:
        return (0, 0, 0)


def is_valid_integer(var: Any) -> bool:
    """
    Checks if variable is integer
    """
    try:
        float(var)
    except TypeError:
        return False # for example var is dictionary
    except ValueError:
        return False
    else:
        return float(var).is_integer()


def tests():
    print("tests..")
    assert dt_make(2025, 2, 28) == "2025-02-28"
    assert is_leap_year(2028) == True
    assert is_leap_year(2000) == True
    assert is_leap_year(1904) == True
    assert is_leap_year(1900) == False

    assert dt_add_years(dt_make(2025, 2, 28), 3) == "2028-02-29"
    assert dt_add_years(dt_make(2025, 2, 28), 3, False) == "2028-02-28"
    assert dt_add_months(dt_make(2025, 3, 29), 1) == "2025-04-29"
    assert dt_add_months(dt_make(2025, 3, 30), 1) == "2025-04-30"
    assert dt_add_months(dt_make(2025, 3, 30), 1, False) == "2025-04-30"
    assert dt_add_months(dt_make(2025, 3, 31), 1) == "2025-04-30"
    assert dt_add_months(dt_make(2025, 3, 31), 1, False) == "2025-04-30"
    assert dt_add_months(dt_make(2025, 3, 29), -1) == "2025-02-28"
    assert dt_add_days(dt_make(2025, 3, 1), 10) == "2025-03-11"

    assert dt_week_start(dt_make(2025, 10, 1)) == dt_make(2025, 9, 29)
    assert dt_week_start(dt_make(2025, 10, 5)) == dt_make(2025, 9, 29)

    assert dt_week_start(dt_make(2025, 10, 1), False) == dt_make(2025, 9, 28)
    assert dt_week_start(dt_make(2025, 10, 5), False) == dt_make(2025, 10, 5)
    assert dt_week_start(dt_make(2025, 10, 4), False) == dt_make(2025, 9, 28)

    assert dt_week_end(dt_make(2025, 10, 1)) == dt_make(2025, 10, 5)
    assert dt_week_end(dt_make(2025, 10, 5)) == dt_make(2025, 10, 5)

    assert dt_week_end(dt_make(2025, 10, 1), False) == dt_make(2025, 10, 4)
    assert dt_week_end(dt_make(2025, 10, 5), False) == dt_make(2025, 10, 11)
    assert dt_week_end(dt_make(2025, 10, 4), False) == dt_make(2025, 10, 4)

    assert dt_quarter_start(dt_make(2025, 1, 1)) == dt_make(2025, 1, 1)
    assert dt_quarter_start(dt_make(2025, 2, 28)) == dt_make(2025, 1, 1)
    assert dt_quarter_start(dt_make(2025, 3, 31)) == dt_make(2025, 1, 1)
    assert dt_quarter_start(dt_make(2026, 12, 31)) == dt_make(2026, 10, 1)

    assert dt_quarter_end(dt_make(2025, 1, 1)) == dt_make(2025, 3, 31)
    assert dt_quarter_end(dt_make(2025, 2, 28)) == dt_make(2025, 3, 31)
    assert dt_quarter_end(dt_make(2025, 3, 31)) == dt_make(2025, 3, 31)
    assert dt_quarter_end(dt_make(2026, 12, 31)) == dt_make(2026, 12, 31)

    assert dt_semiyear_start(dt_make(2025, 1, 1)) == dt_make(2025, 1, 1)
    assert dt_semiyear_start(dt_make(2025, 2, 28)) == dt_make(2025, 1, 1)
    assert dt_semiyear_start(dt_make(2025, 6, 30)) == dt_make(2025, 1, 1)
    assert dt_semiyear_start(dt_make(2025, 7, 1)) == dt_make(2025, 7, 1)
    assert dt_semiyear_start(dt_make(2025, 9, 1)) == dt_make(2025, 7, 1)
    assert dt_semiyear_start(dt_make(2025, 12, 31)) == dt_make(2025, 7, 1)

    assert dt_semiyear_end(dt_make(2025, 1, 1)) == dt_make(2025, 6, 30)
    assert dt_semiyear_end(dt_make(2025, 2, 28)) == dt_make(2025, 6, 30)
    assert dt_semiyear_end(dt_make(2025, 6, 30)) == dt_make(2025, 6, 30)
    assert dt_semiyear_end(dt_make(2025, 7, 1)) == dt_make(2025, 12, 31)
    assert dt_semiyear_end(dt_make(2025, 9, 1)) == dt_make(2025, 12, 31)
    assert dt_semiyear_end(dt_make(2025, 12, 31)) == dt_make(2025, 12, 31)

    assert dt_easter(2000) == dt_make(2000, 4, 23)
    assert dt_easter(2002) == dt_make(2002, 3, 31)
    assert dt_easter(2049) == dt_make(2049, 4, 18)
    assert dt_easter(2071) == dt_make(2071, 4, 19)

    assert dt_easter_gauss(2000) == dt_make(2000, 4, 23)
    assert dt_easter_gauss(2002) == dt_make(2002, 3, 31)
    assert dt_easter_gauss(2049) == dt_make(2049, 4, 18)
    assert dt_easter_gauss(2071) == dt_make(2071, 4, 19)
    
    assert dt_good_friday(2007) == dt_make(2007, 4, 6)
    assert dt_good_friday(2026) == dt_make(2026, 4, 3)
    assert dt_good_friday(2029) == dt_make(2029, 3, 30)
    assert dt_good_friday(2065) == dt_make(2065, 3, 27)

    assert dt_pentecost(2017) == dt_make(2017, 6, 4)
    assert dt_pentecost(2018) == dt_make(2018, 5, 20)
    assert dt_pentecost(2019) == dt_make(2019, 6, 9)
    assert dt_pentecost(2020) == dt_make(2020, 5, 31)

    assert is_valid_integer(1) == True
    assert is_valid_integer(+1) == True
    assert is_valid_integer(-1) == True
    assert is_valid_integer(100.0) == True
    assert is_valid_integer('13') == True
    assert is_valid_integer('17.0') == True
    assert is_valid_integer('+1') == True
    assert is_valid_integer('-1') == True
    assert is_valid_integer(1.13) == False
    assert is_valid_integer('17.63') == False
    assert is_valid_integer('hello world') == False
    assert is_valid_integer({}) == False

    assert dt_add_week(dt_make(2025, 10, 3), 1) == dt_make(2025, 10, 10)
    assert dt_add_week(dt_make(2025, 10, 3), 2) == dt_make(2025, 10, 17)
    assert dt_add_week(dt_make(2025, 10, 3), 3) == dt_make(2025, 10, 24)
    assert dt_add_week(dt_make(2025, 10, 3), 4) == dt_make(2025, 10, 31)
    assert dt_add_week(dt_make(2025, 10, 3), 5) == dt_make(2025, 11, 7)

    assert dt_add_quarter(dt_make(2025, 11, 30), 1) == dt_make(2026, 2, 28)
    assert dt_add_quarter(dt_make(2025, 11, 30), 1, False) == dt_make(2026, 2, 28)
    assert dt_add_quarter(dt_make(2027, 11, 30), 1) == dt_make(2028, 2, 29)
    assert dt_add_quarter(dt_make(2027, 11, 30), 1, False) == dt_make(2028, 2, 29)
    assert dt_add_quarter(dt_make(2026, 2, 28), 1) == dt_make(2026, 5, 31)
    assert dt_add_quarter(dt_make(2026, 2, 28), 1, False) == dt_make(2026, 5, 28)
    assert dt_add_quarter(dt_make(2028, 2, 29), 1) == dt_make(2028, 5, 31)
    assert dt_add_quarter(dt_make(2028, 2, 29), 1, False) == dt_make(2028, 5, 29)
    assert dt_add_quarter(dt_make(2025, 10, 3), -1) == dt_make(2025, 7, 3)
    assert dt_add_quarter(dt_make(2025, 10, 3), -1, False) == dt_make(2025, 7, 3)

    assert dt_add_semiyear(dt_make(2025, 10, 3), 1) == dt_make(2026, 4, 3)
    assert dt_add_semiyear(dt_make(2025, 10, 3), 1, False) == dt_make(2026, 4, 3)
    assert dt_add_semiyear(dt_make(2025, 10, 3), -1) == dt_make(2025, 4, 3)
    assert dt_add_semiyear(dt_make(2025, 10, 3), -1, False) == dt_make(2025, 4, 3)
    assert dt_add_semiyear(dt_make(2026, 2, 28), 1) == dt_make(2026, 8, 31)
    assert dt_add_semiyear(dt_make(2026, 2, 28), 1, False) == dt_make(2026, 8, 28)

    print("...were fine")

if __name__ == '__main__':
    tests()


