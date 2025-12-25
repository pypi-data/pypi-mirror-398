"""
This module provides Hebrew calendar functionality with both text and HTML representations.
It extends the built-in Calendar module to support Hebrew dates and formatting.
"""
#  Copyright (c) 2025 Isaac Dovolsky

import sys
from itertools import repeat
from .hebrewyear import HebrewYear
from calendar import Calendar, HTMLCalendar
from .hebrewdate import HebrewDate, WEEKDAYS, HEBREW_DAYS
from .hebrewmonth import HebrewMonth


class HebrewCalendar(Calendar):
    """A calendar class for working with Hebrew dates.

    Extends the standard `calendar.Calendar` to provide Hebrew calendar functionality,
    including methods for iterating over month days and converting between
    Hebrew and Gregorian dates.

    Args:
        firstweekday (int): The first day of the week (0=Monday, 6=Sunday). Defaults to 1 (Sunday).
        with_gregorian (bool): Whether to include Gregorian dates in the output. Defaults to True.
        with_holidays (bool): Whether to include holidays in the output. Defaults to True.
        with_festive_days (bool): Whether to include festive days. Defaults to False.
        with_fasts (bool): Whether to include fasts. Defaults to False.

    Attributes:
        with_gregorian (bool): Whether to include Gregorian dates.
        with_holidays (bool): Whether to include holidays.
        with_festive_days (bool): Whether to include festive days.
        with_fasts (bool): Whether to include fasts.
    """

    def __init__(self, firstweekday: int = 1, with_gregorian: bool = True, with_holidays: bool = True,
                 with_festive_days: bool = False, with_fasts: bool = False):
        super().__init__(firstweekday)
        self.with_gregorian = with_gregorian
        self.with_holidays = with_holidays
        self.with_festive_days = with_festive_days
        self.with_fasts = with_fasts

    def itermonthdays(self, year, month):
        """Yields day numbers for the specified month and year.

        For days outside the specified month, yields 0.

        Args:
            year (int): Hebrew year.
            month (int): Hebrew month index.

        Yields:
            int: Day number or 0.
        """
        date = HebrewDate(month=month, year=year)
        day1, n_days = date.weekday_numeric, date.year.days[month - 1]
        days_before = (day1 - self.firstweekday) % 7
        yield from repeat(0, days_before)
        yield from range(1, n_days + 1)
        days_after = (self.firstweekday - day1 - n_days) % 7
        yield from repeat(0, days_after)

    def itermonthdays2(self, year, month):
        """Yields day information tuples for the specified month and year.

        Args:
            year (int): Hebrew year.
            month (int): Hebrew month index.

        Yields:
            tuple: (day, weekday, gregorian_day_str, holiday_str).
        """
        for i, d in enumerate(self.itermonthdays(year, month), self.firstweekday):
            date = holiday = ""
            if d != 0:
                h_date = HebrewDate(d, month, year, self.with_festive_days, self.with_fasts)
                if self.with_gregorian:
                    g_date = h_date.to_gregorian()
                    if g_date:
                        date = g_date.strftime("%d")
                if self.with_holidays:
                    holiday = h_date.holiday
            yield d, i % 7, date, holiday


class HTMLHebrewCalendar(HebrewCalendar, HTMLCalendar):
    """HTML representation of the Hebrew calendar.

    Combines `HebrewCalendar` and `calendar.HTMLCalendar` to provide HTML
    formatting. Supports RTL layout, custom CSS styling, and optional
    Gregorian date display.

    Args:
        custom_data (dict, optional): Custom styling and content for specific days.
            Keys are day numbers (1-31), values are dicts with 'classes' (list)
            and 'content' (list).
        firstweekday (int): The first day of the week. Defaults to 1 (Sunday).
        with_gregorian (bool): Include Gregorian dates. Defaults to True.
        with_holidays (bool): Include holidays. Defaults to True.
        with_festive_days (bool): Include festive days. Defaults to False.
        with_fasts (bool): Include fasts. Defaults to False.

    Attributes:
        custom_data (dict): Dictionary of custom day data.
    """
    def __init__(self, custom_data: dict = None, firstweekday=1, with_gregorian=True, with_holidays=True,
                 with_festive_days=False, with_fasts=False):
        HebrewCalendar.__init__(self, firstweekday, with_gregorian, with_holidays, with_festive_days, with_fasts)
        HTMLCalendar.__init__(self, firstweekday)
        self.custom_data = custom_data or {}

    def formatday(self, day, weekday, *args):
        """Returns a day as a table cell (<td>).

        Supports custom data and styling from `self.custom_data`.

        Args:
            day (int): Day number (0 for padding).
            weekday (int): Day of week (0-6).
            *args: Additional content (e.g., Gregorian date, holiday).

        Returns:
            str: HTML table cell.
        """
        if day == 0:
            return f'<td class="{self.cssclass_noday}">&nbsp;</td>'

        # Initialize classes and content
        classes = [self.cssclasses[weekday], 'day']
        content = [f'<div class="date-content">{HEBREW_DAYS[day - 1]}']
        # Add standard data (Gregorian dates and holidays)
        for c in args:
            if c:
                content.append(f'<br>{c}')
        content.append('</div>')
        # Add custom data if present
        if self.custom_data and day in self.custom_data:
            day_data = self.custom_data[day]
            if 'classes' in day_data:
                classes.extend(day_data['classes'])
            if 'content' in day_data:
                content.extend(day_data['content'])
        classes_str = ' '.join(classes)
        content_str = ''.join(content)
        return f'<td class="{classes_str}" data-date="{day}">{content_str}</td>'

    def formatweek(self, week):
        """Returns a complete week as a table row (<tr>).

        Args:
            week (list): List of day information tuples.

        Returns:
            str: HTML table row.
        """
        s = ''.join(self.formatday(d, wd, g, h) for (d, wd, g, h) in week)
        return f'<tr>{s}</tr>'

    def formatweekday(self, day):
        """Returns a weekday name as a table header (<th>).

        Args:
            day (int): Weekday index.

        Returns:
            str: HTML table header.
        """
        return f'<th class="weekday {self.cssclasses_weekday_head[day]}">{WEEKDAYS[day]}</th>'

    def formatmonthname(self, year, month, with_year=True):
        """Returns a month name header row.

        Args:
            year (int): Hebrew year.
            month (int): Hebrew month index.
            with_year (bool): Whether to include the year in the header.

        Returns:
            str: HTML table header section.
        """
        h_year = HebrewYear(year)
        HebrewMonth(h_year, month)
        
        g_info = None
        if self.with_gregorian:
            start_date = HebrewDate(day=1, month=month, year=year)
            end_date = start_date + (h_year.days[month - 1] - 1)
            g_start = start_date.to_gregorian()
            g_end = end_date.to_gregorian()
            
            if g_start or g_end:
                # If only one end is valid, use what we have
                # (e.g. month starts before Gregorian epoch but ends after it)
                g_year = (g_end or g_start).year
                s_name = g_start.strftime('%B') if g_start else ""
                e_name = g_end.strftime('%B') if g_end else ""
                
                if s_name and e_name:
                    gm = f'{s_name}-{e_name}' if s_name != e_name else s_name
                else:
                    gm = s_name or e_name
                g_info = (gm, g_year)

        month_name = h_year.months[month - 1]
        if g_info:
            gm, g_year = g_info
            if with_year:
                s = f'{month_name} {h_year}\n{gm} {g_year}'
            else:
                s = f'{month_name}\n{gm}'
        else:
            if with_year:
                s = f'{month_name} {h_year}'
            else:
                s = str(month_name)
        return f'<thead><tr><th colspan="7" class="{self.cssclass_month_head}">{s}</th></tr></thead>'

    def formatmonth(self, year, month, with_year=True):
        """Returns a formatted month as an HTML table.

        Args:
            year (int): Hebrew year.
            month (int): Hebrew month index.
            with_year (bool): Whether to include the year in the header.

        Returns:
            str: HTML table.
        """
        v = []
        a = v.append
        a(f'<table dir="rtl" border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_month}">')
        a('\n')
        a(self.formatmonthname(year, month, with_year))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(year, month):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)

    def formatyear(self, year, width=3):
        """Returns a formatted year as a table of tables.

        Args:
            year (int): Hebrew year.
            width (int): Number of months per row.

        Returns:
            str: HTML table.
        """
        v = []
        a = v.append
        width = max(width, 1)
        h_year = HebrewYear(year)
        a(f'<table dir="rtl" border="0" cellpadding="0" cellspacing="0" class="{self.cssclass_year}">')
        a('\n')
        a(f'<thead><tr><th colspan="{width}" class="{self.cssclass_year_head}">{h_year}</th></tr></thead>')
        for i in range(1, h_year.month_count + 1, width):
            # months in this row
            months = range(i, min(i + width, 14))
            a('<tr>')
            for m in months:
                a('<td>')
                a(self.formatmonth(year, m, False))
                a('</td>')
            a('</tr>')
        a('</table>')
        return ''.join(v)

    def formatyearpage(self, year, width=3, css="calendar.css", encoding=None):
        """Returns a formatted year as a complete HTML page.

        Args:
            year (int): Hebrew year.
            width (int): Number of months per row.
            css (str): Path to CSS file.
            encoding (str, optional): Output encoding.

        Returns:
            bytes: Encoded HTML page content.
        """
        if encoding is None:
            encoding = sys.getdefaultencoding()
        v = []
        a = v.append
        a(f'<?xml version="1.0" encoding="{encoding}"?>\n')
        a('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n')
        a('<html>\n')
        a('<head>\n')
        a(f'<meta http-equiv="Content-Type" content="text/html; charset={encoding}" />\n')
        if css is not None:
            a(f'<link rel="stylesheet" type="text/css" href="{css}" />\n')
        a(f'<title>Calendar for {HebrewYear.year_to_str(year)}</title>\n')
        a('</head>\n')
        a('<body>\n')
        a(self.formatyear(year, width))
        a('</body>\n')
        a('</html>\n')
        return ''.join(v).encode(encoding, "xmlcharrefreplace")
