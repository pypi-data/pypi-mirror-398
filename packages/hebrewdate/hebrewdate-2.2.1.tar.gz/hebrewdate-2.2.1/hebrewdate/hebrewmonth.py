"""
This module provides the HebrewMonth class, which represents a month in the Hebrew calendar.
"""
#  Copyright (c) 2025 Isaac Dovolsky

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .hebrewyear import HebrewYear

STANDARD_MONTHS = {
    "תשרי": 30, "חשוון": 29, "כסלו": 30, "טבת": 29, "שבט": 30, "אדר": 29,
    "ניסן": 30, "אייר": 29, "סיוון": 30, "תמוז": 29, "אב": 30, "אלול": 29
}
LEAP_MONTHS = {
    "תשרי": 30, "חשוון": 29, "כסלו": 30, "טבת": 29, "שבט": 30, "אדר א": 30,
    "אדר ב": 29, "ניסן": 30, "אייר": 29, "סיוון": 30, "תמוז": 29, "אב": 30,
    "אלול": 29
}

class HebrewMonth:
    """Represents a Hebrew month.

    Provides information about its name, index, and length, and supports
    comparisons with strings, integers, and other HebrewMonth objects.

    Args:
        year (HebrewYear): The HebrewYear object this month belongs to.
        month (int | str): The month index (1-based) or month name.

    Attributes:
        year (HebrewYear): The HebrewYear object this month belongs to.
        index (int): The 1-based index of the month.
        name (str): The name of the month.
    """

    def __init__(self, year: HebrewYear, month: int | str):
        self.year = year
        
        month_names = self.year.month_names
        if isinstance(month, int):
            if month < 1 or month > self.year.month_count:
                raise ValueError(f"bad month value '{month}'")
            self.index = month
            self.name = month_names[month - 1]
        elif isinstance(month, str):
            try:
                self.index = month_names.index(month) + 1
                self.name = month
            except ValueError:
                raise ValueError(f"bad month value '{month}'")
        else:
            raise TypeError("Invalid month type")

    @property
    def length(self) -> int:
        """Returns the number of days in the month.

        Returns:
            int: Number of days.
        """
        return self.year.days[self.index - 1]

    def __repr__(self) -> str:
        return f"HebrewMonth({self.name}, {self.year.year})"

    def __str__(self) -> str:
        return self.name

    def __int__(self) -> int:
        return self.index

    def __eq__(self, other: object) -> bool:
        """Checks equality against HebrewMonth, int (index), or str (name)."""
        if isinstance(other, HebrewMonth):
            return self.index == other.index and self.year == other.year
        if isinstance(other, int):
            return self.index == other
        if isinstance(other, str):
            return self.name == other
        return False

    def __iter__(self):
        """Yields (index, name)."""
        return iter((self.index, self.name))
