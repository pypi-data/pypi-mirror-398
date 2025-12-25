"""
This module provides the HebrewYear class, which represents the Hebrew calendar year.

The class includes methods for determining if a year is a leap year, calculating the total
number of days in a year, computing the individual months and their lengths, and determining
the first weekday of the year. Additionally, it calculates the schedule of new moons and supports
operations such as year arithmetic and comparisons.
"""
#  Copyright (c) 2025 Isaac Dovolsky

from __future__ import annotations
from functools import lru_cache
import re
from .hebrewmonth import HebrewMonth, STANDARD_MONTHS, LEAP_MONTHS

FIRST_NEW_MOON = 57444  # First new moon time in parts
NEW_MOON_INTERVAL = 765433  # Interval between new moons in parts
INVALID_FIRST_DAYS = {1, 4, 6}  # Invalid first days of the Hebrew year


@lru_cache(maxsize=128)
def _get_year_data(year: int):
    """Calculates and caches basic year data."""
    is_leap = HebrewYear.is_leap_year(year)
    months_dict = LEAP_MONTHS if is_leap else STANDARD_MONTHS
    month_names = tuple(months_dict.keys())
    month_days = tuple(months_dict.values())
    month_count = 13 if is_leap else 12
    return is_leap, month_names, month_days, month_count


def _validate_year(year: int | str) -> int:
    if isinstance(year, str):
        year = HebrewYear.str_to_year(year)
    if year < 1 or year > 9999:
        raise ValueError(f"bad year value {year}")
    return year


class HebrewYear:
    """Represents a Hebrew year.

    Handles leap years, calendar calculations, and conversions between numeric
    and traditional Hebrew string representations.

    Args:
        year (int | str): Numeric value of the year (1-9999) or Hebrew string.

    Attributes:
        year (int): Numeric value of the Hebrew year.
        year_str (str): Traditional Hebrew string representation.
        is_leap (bool): Whether the year is a leap year.
        months (list[HebrewMonth]): List of HebrewMonth objects for the year.
        days (list[int]): Number of days in each month.
        month_count (int): Total number of months in the year (12 or 13).
        first_weekday (int): The numeric weekday of Rosh Hashanah (0-6, Sat-Fri).
    """

    def __init__(self, year: int | str):
        self.year = _validate_year(year)
        self.year_str = self.year_to_str(self.year)
        self.is_leap, self.month_names, self.month_days, self.month_count = _get_year_data(self.year)
        self.first_weekday = self._first_weekday()
        self.days = list(self.month_days)
        self._calculate_days()
        self._total_days = sum(self.days)
        self.cumulative_days = [0]
        for d in self.days:
            self.cumulative_days.append(self.cumulative_days[-1] + d)
        self.months = [HebrewMonth(self, i + 1) for i in range(self.month_count)]

    def __repr__(self) -> str:
        return f"Year({self.year_str})"

    def __str__(self) -> str:
        return self.year_str

    def __int__(self) -> int:
        return self.year

    def __eq__(self, other: int | HebrewYear) -> bool:
        return self.year == int(other)

    def __ne__(self, other: int | HebrewYear) -> bool:
        return self.year != int(other)

    def __gt__(self, other: int | HebrewYear) -> bool:
        return self.year > int(other)

    def __lt__(self, other: int | HebrewYear) -> bool:
        return self.year < int(other)

    def __ge__(self, other: int | HebrewYear) -> bool:
        return self.year >= int(other)

    def __le__(self, other: int | HebrewYear) -> bool:
        return self.year <= int(other)

    def __len__(self) -> int:
        return self.month_count

    def __add__(self, other: int) -> HebrewYear:
        if isinstance(other, int):
            return HebrewYear(self.year + other)
        raise ValueError(f"Unsupported operand type(s) for +: 'Year' and {type(other).__name__}")

    def __sub__(self, other: int | HebrewYear) -> int | HebrewYear:
        if isinstance(other, int):
            return HebrewYear(self.year - other)
        if isinstance(other, HebrewYear):
            return self.year - other.year
        raise ValueError(f"Unsupported operand type(s) for -: 'Year' and {type(other).__name__}")

    @staticmethod
    def is_leap_year(year: int) -> bool:
        """Determines if a given year is a leap year.

        Args:
            year (int): The Hebrew year to check.

        Returns:
            bool: True if it's a leap year, False otherwise.
        """
        return (1 << (year % 19)) & 0x24949 != 0  # Bitmask for {0, 3, 6, 8, 11, 14, 17}

    def total_days(self) -> int:
        """Returns the total number of days in the year.

        Returns:
            int: Total day count.
        """
        try:
            return self._total_days
        except AttributeError:
            return sum(self.days)

    def month_dict(self) -> dict[str, int]:
        """Returns a dictionary mapping month names to their lengths.

        Returns:
            dict[str, int]: Month names and day counts.
        """
        return dict(zip(self.month_names, self.days))

    def new_moons(self) -> dict[str, str]:
        """Calculates the schedule of new moons for each month.

        Returns:
            dict[str, str]: Month names and formatted Molad times (d:h:p).
        """
        first_new_moon = self.first_new_moon() % 181440  # 7 * 24 * 1080 = 181440
        return {
            self.month_names[month]: (
                f'{(month * NEW_MOON_INTERVAL + first_new_moon) // 1080 // 24 % 7}:'
                f'{(month * NEW_MOON_INTERVAL + first_new_moon) // 1080 % 24}:'
                f'{(month * NEW_MOON_INTERVAL + first_new_moon) % 1080}'
            )
            for month in range(self.month_count)
        }

    def first_new_moon(self, year: int = None) -> int:
        """Returns the time of the year's first new moon in parts since epoch.

        Args:
            year (int, optional): The year to calculate for. Defaults to current year.

        Returns:
            int: Total parts.
        """
        year = (self.year if year is None else year) - 1
        # Number of leap years up to the current year
        # Leap years are years 3, 6, 8, 11, 14, 17, 19 in the 19-year cycle
        # We use a bitmask or set to count leap years in the current cycle
        cycle, year_in_cycle = divmod(year, 19)
        leap_years = cycle * 7 + sum(1 for j in (3, 6, 8, 11, 14, 17, 19) if j <= year_in_cycle)
        # Total new moons up to the first new moon of the current year
        return (year * 12 + leap_years) * NEW_MOON_INTERVAL + FIRST_NEW_MOON

    def _first_weekday(self, year: int = None) -> int:
        """ Calculates the first weekday of the year. """
        year = self.year if year is None else year
        first_nm = self.first_new_moon(year)
        first_nmh = (first_nm // 1080) % 24
        first_day = (first_nm // 1080 // 24) % 7
        if first_day == 2 and self.is_leap_year(year - 1):
            if first_nmh == 15 and first_nm % 1080 >= 589 or first_nmh >= 16:
                first_day = 3
        elif first_day == 3 and not self.is_leap_year(year):
            if first_nmh == 9 and first_nm % 1080 >= 204 or first_nmh >= 10:
                first_day = 5
        elif first_nmh >= 18:
            first_day = (first_day + 1) % 7
        if first_day in INVALID_FIRST_DAYS:
            first_day = (first_day + 1) % 7
        return first_day

    def _calculate_days(self):
        """ Calculates the number of days in Heshvan and Kislev """
        if self.first_weekday != 3:
            next_theoretical = (self.total_days() + self.first_weekday) % 7
            next_actual = self._first_weekday(self.year + 1)
            if next_theoretical < next_actual or next_theoretical == 6 and next_actual == 0:
                self.days[1] = 30
            elif next_theoretical > next_actual or next_theoretical == 0 and next_actual == 1:
                self.days[1] = self.days[2] = 29

    @staticmethod
    def year_to_str(year: int) -> str:
        """
        Convert a numeric Hebrew year to its traditional Hebrew string representation.

        **year**: ``int``
            The numeric Hebrew year to convert (1-9999)
        """
        if year < 1 or year > 9999:
            raise ValueError(f"bad year value {year}")
        parts = []
        thousands, year = divmod(year, 1000)
        hundreds, year = divmod(year, 100)
        # Special case 400
        while hundreds >= 4:
            parts.append(chr(1514))  # ת
            hundreds -= 4
        # Hundreds
        if hundreds:
            parts.append(chr(1510 + hundreds))
        # Special cases for 15 and 16
        if year == 15:
            parts.extend(['ט', 'ו'])
        elif year == 16:
            parts.extend(['ט', 'ז'])
        else:
            tens, year = divmod(year, 10)
            # Tens
            if tens:
                tens = 1496 + tens + (tens // 2)
                parts.append(chr(tens + 1 if tens in (1503, 1509) else tens))
            # Units
            if year:
                parts.append(chr(1487 + year))
        # Add gershayim/geresh
        if len(parts) >= 2:
            parts[-2] += '"'  # Gershayim before last letter

        return (f"{chr(1487 + thousands)}'" if thousands else '') + ''.join(parts)
    
    @staticmethod
    def str_to_year(s: str) -> int:
        """
        Convert a Hebrew year string to its numeric value.

        **s**: ``str``
            The Hebrew year string to convert.
        """
        # Hebrew letter values
        values = {
            'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
            'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
            'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400
        }
        
        # Clean the string
        s_clean = s.replace('"', '').replace('\'', ' ').strip()
        parts = s_clean.split(' ')
        
        year = 0
        if len(parts) > 1:
            # Thousands part
            year += values.get(parts[0], 0) * 1000
            s_rest = parts[1]
        elif '\'' in s and s.index('\'') < 3 and len(s) > 1:
            # Thousands part with geresh but no space
            geresh_idx = s.index('\'')
            year += values.get(s[geresh_idx-1], 0) * 1000
            s_rest = s[geresh_idx+1:].replace('"', '')
        else:
            s_rest = parts[0]
            # Handle cases like "א'" which mean 1000
            if s.endswith("'") and len(s) <= 2:
                 return values.get(s[0], 0) * 1000

        for char in s_rest:
            year += values.get(char, 0)
            
        return year
