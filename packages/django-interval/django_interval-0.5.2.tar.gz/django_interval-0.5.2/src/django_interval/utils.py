from typing import Optional, Tuple
import calendar
import math
import re
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class DateTuple:
    sort_date: datetime = None
    from_date: datetime = None
    to_date: datetime = None

    def __bool__(self):
        return any(
            elem is not None for elem in [self.sort_date, self.from_date, self.to_date]
        )

    def tuple(self):
        return self.sort_date, self.from_date, self.to_date

    def set_range(self, from_date, to_date):
        self.from_date = from_date
        self.to_date = to_date
        if self.from_date > self.to_date:
            raise ValueError("`from` date must be earlier than `to` date'")
        days_delta_half = math.floor((self.to_date - self.from_date).days / 2)
        self.sort_date = self.from_date + timedelta(days=days_delta_half)


def parse_single_date(
    datestring: str,
) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    datestring = datestring.replace(" ", "")
    datestring = datestring.replace("-", ".").replace("/", ".").replace("\\", ".")
    year, month, day = None, None, None

    if re.match(r"\d{3,4}$", datestring):
        # year
        year = int(datestring)
    elif re.match(r"\d{1,2}\.\d{3,4}$", datestring):
        # month - year
        tmp = re.split(r"\.", datestring)
        month = int(tmp[0])
        year = int(tmp[1])
    elif re.match(r"\d{1,2}\.\d{1,2}\.\d{3,4}$", datestring):
        # day - month - year
        tmp = re.split(r"\.", datestring)
        day = int(tmp[0])
        month = int(tmp[1])
        year = int(tmp[2])
    elif re.match(r"\d{3,4}\.\d{1,2}\.?$", datestring):
        # year - month
        tmp = re.split(r"\.", datestring)
        year = int(tmp[0])
        month = int(tmp[1])
    elif re.match(r"\d{3,4}\.\d{1,2}\.\d{1,2}\.?$", datestring):
        # year - month - day
        tmp = re.split(r"\.", datestring)
        year = int(tmp[0])
        month = int(tmp[1])
        day = int(tmp[2])

    if year is None:
        raise ValueError("Could not interpret date.")

    return year, month, day


def parse_date_range_individual(datestring: str, ab=False, bis=False):
    if ab and bis:
        raise ValueError("Could not interpret date.")

    year, month, day = parse_single_date(datestring)

    if not ab and not bis and (month is None or day is None):
        if month is None:
            month_ab = 1
            month_bis = 12
        else:
            month_ab = month
            month_bis = month
        if day is None:
            day_ab = 1
            day_bis = calendar.monthrange(year, month_bis)[1]
        else:
            day_ab = day
            day_bis = day

        return (
            datetime(year=year, month=month_ab, day=day_ab),
            datetime(year=year, month=month_bis, day=day_bis),
        )
    else:
        if month is None:
            if ab and not bis:
                month = 1
            elif not ab and bis:
                month = 12
        if day is None:
            if ab and not bis:
                day = 1
            elif not ab and bis:
                day = calendar.monthrange(year, month)[1]

        return datetime(year=year, month=month, day=day)


def parse_angle_brackets(date_string: str) -> DateTuple:
    """
    Identify ISO dates in a (sub)string enclosed in angled brackets and
    assign them to DateTuple's fields.

    Only single dates and sets of three dates (separated by commas)
    are considered valid; other numbers of dates will raise an error.
    When a single date is found, it is used as DateTuple's sort_date value.
    When the string in angled brackets is made up of three dates, they are
    assigned to DateTuple's fields in the order: sort_date, from_date, to_date

    Examples for valid inputs:
        < 2013-07-11, 2013-07-11, 2013-08-20 >
        <1980-W04-4,1980-W01,1980-W08>
        <19991231>
    """
    dates = DateTuple()
    if match := re.match(r".*<(?P<dates>.*)>.*", date_string):
        match match.group("dates").split(","):
            case [date_sort_string, date_from_string, date_to_string]:
                dates.sort_date = datetime.fromisoformat(date_sort_string.strip())
                dates.from_date = datetime.fromisoformat(date_from_string.strip())
                dates.to_date = datetime.fromisoformat(date_to_string.strip())
            case [date_sort_string]:
                dates.sort_date = datetime.fromisoformat(date_sort_string.strip())
            case _:
                raise ValueError(
                    "Incorrect number of dates given. Within angled brackets, "
                    "only either one or three dates (separated by commas) are "
                    "allowed."
                )
    return dates


def parse_human(date_string: str) -> DateTuple:
    dates = DateTuple()
    date_string = date_string.lower()
    match re.findall(r"(?:ab (?P<from>\S*))", date_string):
        case [date_from_string]:
            dates.from_date = parse_date_range_individual(date_from_string, ab=True)
        case [head, *elements]:
            from_dates = ", ".join(elements)
            raise ValueError(f"Redundant from dates found: {head}, {from_dates}")
    match re.findall(r"(?:bis (?P<to>\S*))", date_string):
        case [date_to_string]:
            dates.to_date = parse_date_range_individual(date_to_string, bis=True)
        case [head, *elements]:
            to_dates = ", ".join(elements)
            raise ValueError(f"Redundant to dates found: {head}, {to_dates}")
    if "ab" not in date_string and "bis" not in date_string:
        date_sort = parse_date_range_individual(date_string)
        if type(date_sort) is tuple:
            dates.set_range(*date_sort)
        else:
            dates.sort_date = dates.from_date = dates.to_date = date_sort
    if bool(dates.from_date) != bool(dates.to_date):
        dates.sort_date = dates.from_date or dates.to_date
    return dates


def defaultdateparser(date_string: str) -> Tuple[datetime, datetime, datetime]:
    try:
        dates = parse_angle_brackets(date_string) or parse_human(date_string)
        return dates.tuple()
    except Exception as e:
        print("Could not parse date: '", date_string, "' due to error: ", e)

    return None, None, None
