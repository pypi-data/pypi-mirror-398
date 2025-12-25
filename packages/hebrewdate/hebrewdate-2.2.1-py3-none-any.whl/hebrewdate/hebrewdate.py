"""
This module provides functionality for working with Hebrew dates.
It enables the representation of Hebrew dates, conversions between Hebrew and Gregorian calendars, 
and various date arithmetic operations.
"""
#  Copyright (c) 2025 Isaac Dovolsky

from __future__ import annotations
import warnings
import datetime as dt
from .holidays import get_holiday
from .hebrewyear import HebrewYear
from .hebrewmonth import HebrewMonth

EPOCH_H_DATE = (14, 4, 5512)  # Hebrew date of Gregorian epoch (14 Tevet 5512)
EPOCH_G_DATE = (1752, 1, 1)   # Corresponding Gregorian epoch
G_BOUNDARY = (18, 4, 3761)    # Hebrew date of proleptic Gregorian epoch (0001-01-01)

# Hebrew Days and Weekdays
HEBREW_DAYS = (
    "א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י", "יא", "יב", "יג", "יד",
    "טו", "טז", "יז", "יח", "יט", "כ", "כא", "כב", "כג", "כד", "כה", "כו", "כז",
    "כח", "כט", "ל"
)
WEEKDAYS = ("שבת", "ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי")

def _validate_day(day, month: HebrewMonth, year: HebrewYear) -> str:
    if isinstance(day, int):
        if day < 1 or day > month.length:
            raise ValueError(f"bad day value '{day}' for {month.length}-day month")
        day = HEBREW_DAYS[day - 1]
    elif isinstance(day, str):
        day = day.replace('"', '')
        if day not in HEBREW_DAYS:
            raise ValueError(f"bad day value '{day}'")
    else:
        raise TypeError("Invalid day type")
    return day


class HebrewDate:
    """Represents a Hebrew date.

    Supports conversions between Hebrew and Gregorian calendars, date arithmetic,
    and holiday identification.

    Args:
        day (int | str, optional): Day of the month (1-30 or Hebrew string). Defaults to 1.
        month (int | str, optional): Month (1-12/13 or name). Defaults to 1.
        year (int | str, optional): Year (1-9999 or Hebrew string). Defaults to current.
        include_festive_days (bool, optional): Include festive days (e.g. Hanukkah). Defaults to False.
        include_fasts (bool, optional): Include fast days. Defaults to False.

    Attributes:
        year (HebrewYear): HebrewYear object for the date's year.
        year_numeric (int): Numeric value of the year.
        month (str): Name of the month.
        hebrew_month (HebrewMonth): HebrewMonth object for the date's month.
        month_numeric (int): 1-based index of the month.
        day (str): Hebrew string representation of the day.
        day_numeric (int): Day of the month (1-30).
        weekday (str): Name of the weekday.
        weekday_numeric (int): Weekday index (1=Sunday, 7=Saturday).
        genesis (int): Numeric representation in parts since epoch.
        include_festive_days (bool): Whether to include festive days in holiday property.
        include_fasts (bool): Whether to include fasts in holiday property.
    """

    def __init__(self, day: int | str = None, month: int | str = None, year: int | str = None,
                 include_festive_days: bool = False, include_fasts: bool = False):
        if year is None:
            if day is not None and month is not None:
                raise ValueError("If both `day` and `month` are provided, then `year` must also be provided.")
            _d, _m, year = self.today()
            if day is None and month is None:
                day, month = _d, _m

        self.year = HebrewYear(year)
        self.hebrew_month = HebrewMonth(self.year, 1 if month is None else month)
        self.month = self.hebrew_month.name
        self.day = _validate_day(1 if day is None else day, self.hebrew_month, self.year)

        self.year_numeric = self.year.year
        self.month_numeric = self.hebrew_month.index
        self.day_numeric = HEBREW_DAYS.index(self.day) + 1

        days_before = self.days_before()
        weekday = (days_before + self.year.first_weekday) % 7
        self.weekday = WEEKDAYS[weekday]
        self.weekday_numeric = (7 if weekday == 0 else weekday)

        # genesis is Rosh Hashanah of the year + days_before
        # first_weekday is 0=Sat, 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri
        # Hebrew Epoch (Genesis) is 1 Tishrei 1, which corresponds to first_new_moon(1)
        # But our genesis is parts since epoch.
        # We can calculate it more directly.
        self.genesis = (self.year.first_new_moon() // 25920) * 25920
        molad_day = (self.year.first_new_moon() // 25920) % 7
        day_diff = (self.year.first_weekday - molad_day) % 7
        self.genesis += (day_diff + days_before) * 25920

        self.include_festive_days = include_festive_days
        self.include_fasts = include_fasts
        self._is_holiday, self._holiday = get_holiday(self, include_festive_days, include_fasts)

    def __repr__(self) -> str:
        return f"HebrewDate({self.__str__()})"

    def __str__(self) -> str:
        return f"יום {self.weekday} {self.day} {self.month} {self.year}"

    def __int__(self) -> int:
        return self.genesis

    def __eq__(self, other: int | float | HebrewDate) -> bool:
        return int(self) == int(other)

    def __ne__(self, other: int | float | HebrewDate) -> bool:
        return int(self) != int(other)

    def __lt__(self, other: int | float | HebrewDate) -> bool:
        return int(self) < int(other)

    def __gt__(self, other: int | float | HebrewDate) -> bool:
        return int(self) > int(other)

    def __le__(self, other: int | float | HebrewDate) -> bool:
        return int(self) <= int(other)

    def __ge__(self, other: int | float | HebrewDate) -> bool:
        return int(self) >= int(other)

    def __add__(self, other) -> HebrewDate:
        if isinstance(other, (int, float)):
            parts = int(other) * 25920
            target_genesis = self.genesis + parts
            
            # Estimate year more accurately: 1 year is approx 354.37 days
            days = int(other)
            if abs(days) < 30:
                # Same or adjacent month
                new_year_num = self.year_numeric
                new_month = self.month_numeric - 1
                new_day = self.day_numeric + days
            else:
                new_year_num = self.year_numeric + int(days / 354.37)
                if new_year_num < 1 or new_year_num > 9999:
                     raise ValueError(f"Resulting year {new_year_num} is out of range (1-9999)")
                
                new_year = HebrewYear(new_year_num)
                new_month = 0
                new_day = (target_genesis - (new_year.first_new_moon() // 25920) * 25920) // 25920
                molad_day = (new_year.first_new_moon() // 25920) % 7
                day_diff = (new_year.first_weekday - molad_day) % 7
                new_day -= day_diff
                new_day += 1 # 1-based day

            new_year = HebrewYear(new_year_num)
            while new_day < 1:
                new_month -= 1
                if new_month < 0:
                    new_year_num -= 1
                    if new_year_num < 1:
                        raise ValueError("Resulting date is before Hebrew Year 1")
                    new_year = HebrewYear(new_year_num)
                    new_month = new_year.month_count - 1
                new_day += new_year.days[new_month]
            while new_day > new_year.days[new_month]:
                new_day -= new_year.days[new_month]
                new_month += 1
                if new_month >= new_year.month_count:
                    new_year_num += 1
                    if new_year_num > 9999:
                        raise ValueError("Resulting year is after 9999")
                    new_year = HebrewYear(new_year_num)
                    new_month = 0
            
            return HebrewDate(day=new_day, month=new_month + 1, year=new_year_num,
                             include_festive_days=self.include_festive_days,
                             include_fasts=self.include_fasts)
        raise TypeError(f"Unsupported operand type(s) for +: 'HebrewDate' and {type(other).__name__}")

    def __sub__(self, other) -> int | HebrewDate:
        if isinstance(other, (int, float)):
            return self + (-int(other))
        if isinstance(other, HebrewDate):
            return (self.genesis - other.genesis) // 25920
        raise TypeError(f"Unsupported operand type(s) for -: 'HebrewDate' and {type(other).__name__}")

    def __iter__(self):
        """Yields (day_numeric, month_numeric, year_numeric)."""
        return iter((self.day_numeric, self.month_numeric, self.year_numeric))

    @property
    def is_holiday(self) -> bool:
        """Returns whether the current date is a Hebrew holiday.

        Returns:
            bool: True if it's a holiday, False otherwise.
        """
        return self._is_holiday

    @property
    def holiday(self) -> str:
        """Returns the name of the Hebrew holiday.

        Returns:
            str: Holiday name or empty string.
        """
        return self._holiday

    def get_month_tuple(self) -> tuple[int, str]:
        """Returns the month number and name.

        Returns:
            tuple[int, str]: (index, name).
        """
        return self.month_numeric, self.month

    def get_day_tuple(self) -> tuple[int, str]:
        """Returns the day number and Hebrew string representation.

        Returns:
            tuple[int, str]: (index, day_str).
        """
        return self.day_numeric, self.day

    def get_weekday_tuple(self) -> tuple[int, str]:
        """Returns the weekday number and name.

        Returns:
            tuple[int, str]: (index, name).
        """
        return self.weekday_numeric, self.weekday

    def days_before(self) -> int:
        """Calculates the number of days from the start of the year to this date.

        Returns:
            int: Number of days.
        """
        return self.year.cumulative_days[self.month_numeric - 1] + self.day_numeric - 1

    def days_after(self) -> int:
        """Calculates the number of days from this date to the end of the year.

        Returns:
            int: Number of days.
        """
        return self.year.total_days() - self.days_before() - 1

    def delta(self, days: int = 0, months: int = 0, years: int = 0) -> HebrewDate:
        """Computes a new HebrewDate offset by the given days, months, and years.

        Args:
            days (int): Day offset.
            months (int): Month offset.
            years (int): Year offset.

        Returns:
            HebrewDate: New date instance.
        """
        if months == 0 and years == 0:
            return self + days

        # Adjust the Year
        new_year_num = self.year_numeric + years
        if new_year_num < 1 or new_year_num > 9999:
            raise ValueError(f"Resulting year {new_year_num} is out of range (1-9999)")
        new_year = HebrewYear(new_year_num)

        # Adjust the Month
        new_month_idx = self.month_numeric - 1 + months  # Convert to 0-based index
        while new_month_idx < 0:  # Handle underflow
            new_year_num -= 1
            if new_year_num < 1:
                raise ValueError("Resulting date is before Hebrew Year 1")
            new_year = HebrewYear(new_year_num)
            new_month_idx += new_year.month_count
        while new_month_idx >= new_year.month_count:  # Handle overflow
            new_month_idx -= new_year.month_count
            new_year_num += 1
            if new_year_num > 9999:
                raise ValueError("Resulting year is after 9999")
            new_year = HebrewYear(new_year_num)

        # Adjust the Day
        new_day = self.day_numeric + days
        while new_day < 1:  # Handle day underflow
            new_month_idx -= 1
            if new_month_idx < 0:
                new_year_num -= 1
                if new_year_num < 1:
                    raise ValueError("Resulting date is before Hebrew Year 1")
                new_year = HebrewYear(new_year_num)
                new_month_idx = new_year.month_count - 1
            new_day += new_year.days[new_month_idx]
        while new_day > new_year.days[new_month_idx]:  # Handle day overflow
            new_day -= new_year.days[new_month_idx]
            new_month_idx += 1
            if new_month_idx >= new_year.month_count:
                new_year_num += 1
                if new_year_num > 9999:
                    raise ValueError("Resulting year is after 9999")
                new_year = HebrewYear(new_year_num)
                new_month_idx = 0
        return HebrewDate(day=new_day, month=new_month_idx + 1, year=new_year_num,
                          include_festive_days=self.include_festive_days,
                          include_fasts=self.include_fasts)

    @classmethod
    def from_gregorian(cls, day: int = None, month: int = None, year: int = None, date: dt.date = None) -> HebrewDate:
        """Creates a HebrewDate object from a Gregorian date.

        Args:
            day (int, optional): Gregorian day.
            month (int, optional): Gregorian month.
            year (int, optional): Gregorian year.
            date (dt.date, optional): Date object.

        Returns:
            HebrewDate: Corresponding Hebrew date.

        Raises:
            ValueError: If insufficient arguments are provided.
            TypeError: If date is not dt.date.
        """
        if day and month and year:
            date = dt.date(year, month, day)
        elif date is None:
            raise ValueError("Provide either a valid `date` or `day`, `month`, and `year` arguments.")
        if date.year < 1752:
            warnings.warn("Hebrew dates may be inaccurate for years earlier than 1752.", RuntimeWarning, 2)
        return cls(*EPOCH_H_DATE) + (date - dt.date(*EPOCH_G_DATE)).days

    def to_gregorian(self) -> dt.date | None:
        """Converts the current HebrewDate object to a Gregorian date.

        Returns:
            dt.date | None: Gregorian date or None if conversion fails.
        """
        try:
            date = dt.date(*EPOCH_G_DATE) + dt.timedelta(days=(self - HebrewDate(*EPOCH_H_DATE)))
            if date.year < 1752:
                warnings.warn(
                    "Hebrew dates may be inaccurate for years earlier than 1752.", RuntimeWarning, 2)
            return date
        except OverflowError:
            warnings.warn(
                "The Hebrew date is too far in the past to convert to a Gregorian date.", RuntimeWarning, 2)
            return None

    @classmethod
    def today(cls) -> HebrewDate:
        """Returns the current Hebrew date.

        Returns:
            HebrewDate: Today's date.
        """
        return cls.from_gregorian(date=dt.date.today())
