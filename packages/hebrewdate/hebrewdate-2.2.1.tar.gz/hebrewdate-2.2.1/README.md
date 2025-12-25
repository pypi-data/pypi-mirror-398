# hebrewdate
A comprehensive Python library for working with the Hebrew calendar, providing date conversions, calendar generation, and holiday information.

## Key Features
- **Conversion**: Seamlessly convert between Hebrew and Gregorian dates.
- **Holidays**: Built-in support for major holidays, festive days (Chol HaMoed, Hanukkah), and fasts.
- **Arithmetic**: Easily add or subtract days, months, or years from Hebrew dates.
- **Calendar**: Generate text or HTML calendars for any Hebrew month or year.
- **Leap Years**: Full handling of the 19-year Hebrew calendar cycle.
- **Traditional Formatting**: Support for traditional Hebrew year strings (e.g., ה'תשפ"ה).

## Installation
```bash
pip install hebrewdate
```

## Quick Start

### Basic Date Operations
```python
from hebrewdate import HebrewDate

# Get today's Hebrew date
today = HebrewDate.today()
print(today)  # יום חמישי יט כסלו ה'תשפ"ה

# Create a specific Hebrew date
date = HebrewDate(15, "ניסן", 5785)
print(date.to_gregorian())  # 2025-04-13

# Date arithmetic
next_week = date + 7
print(next_week)  # יום ראשון כב ניסן ה'תשפ"ה

# Check for holidays
if date.is_holiday:
    print(f"Today is {date.holiday}")  # Today is יו"ט ראשון של פסח
```

### Working with Years and Months
```python
from hebrewdate import HebrewYear, HebrewMonth

# Explore a Hebrew year
year = HebrewYear(5784)
print(year.is_leap)  # True
print(year.month_count)  # 13

# Explore a Hebrew month
month = HebrewMonth(year, "אדר א")
print(month.length)  # 30
```

### Generating HTML Calendars
```python
from hebrewdate import HTMLHebrewCalendar

# Create an HTML calendar for Tishrei 5785
cal = HTMLHebrewCalendar(with_gregorian=True, with_holidays=True)
html = cal.formatmonth(5785, 1)

# Save to file
with open("calendar.html", "w", encoding="utf-8") as f:
    f.write(html)
```

## Limitations
- Supported Python versions: 3.9 and later.
- Date conversions before 1752 CE may be slightly inaccurate due to historical calendar variations.
- Extremely ancient dates might not be convertible to the Gregorian system.

## License
This project is licensed under the MIT License.

## Author
Isaac Dovolsky
