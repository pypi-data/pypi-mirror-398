# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.1] - 22-12-2025

### Fixed
- UndO AI introduced error in Hanukkah length calculation
- Undo AI introduced error in Purim date calculations
- Tests fixed accordingly

## [2.2.0] - 18-12-2025

### Optimized
- Optimized `HebrewYear` with `lru_cache` for year data and more efficient leap year checking.
- Optimized `HebrewDate` arithmetic operations (`__add__`, `__sub__`, `delta`) to reduce redundant calculations.
- Improved `HebrewMonth` initialization efficiency.
- Refined `get_holiday` logic for better performance by avoiding unnecessary dictionary lookups and object creation.

### Added
- New `HebrewMonth` class to encapsulate month-specific logic and validation.
- Comprehensive test suite covering extreme years (1-9999), edge case holidays (Purim Meshulash, Hanukkah length, Tu B'Av), and various Hebrew year string formats.
- Partial Gregorian date support for calendar months at the start of the proleptic Gregorian epoch (Year 1).

### Changed
- Refactored `HebrewYear` and `HebrewDate` to use the new `HebrewMonth` class.
- Improved Hebrew year string parsing (`str_to_year`) to support all Hebrew letters and more flexible formatting.
- Consistent Google-style docstrings applied across the entire project for better documentation.
- Updated `README.md` with better examples and a clearer Quick Start guide.

### Fixed
- Off-by-one error in Hebrew to Gregorian conversion.
- Epoch alignment in `HebrewDate.genesis` to correctly match Rosh Hashanah postponements.
- Holiday mapping for Adar in leap years (Adar I/II now correctly identify Purim/fasts).
- Hanukkah length calculation in years where Kislev has 29 days.

## [2.1.0] - 05-08-2025

### Added

- `HebrewDate` now holds `include_festive_days` and `include_fasts` as attributes that can be changed after
   instantiation.
- `HebrewDate` is now iterable, yielding the `day_numeric`, `month_numeric` and `year_numeric` attributes.

### Changed

- ⚠️ **IMPORTANT:** Changed `HebrewDate` initialization behavior: 
    If both day and month are passed, then year must also be passed.
    If neither day, month nor year are passed, then the current date will be used,
    which makes the default constructor equivalent to `HebrewDate.today()`.
    Finally, if only day or month are not passed, then they are set to the first day or the first month respectively.
- methods: `HebrewDate.get_month`, `HebrewDate.get_day` and `HebrewDate.get_weekday` got suffixed with `_tuple`
- `HebrewDate.is_holiday` and `HebrewDate.holiday` are now dynamic properties instead of attributes

### Fixed

- Validation logic for `HebrewDate`

## [2.0.4] - 27-06-2025

### Changed

- Test cases

### Fixed

- `HebrewCalendar` and `HTMLHebrewCalendar` didn't check if date is out of Gregorian range
- `HTMLHebrewCalendar` erroneous calculation in formatmonthname

## [2.0.1] - 27-06-2025

### Added

- Added support for Hebrew holidays, festive days, and fasting days
- Enhanced HTML calendar formatting with holidays
- Improved CSS customization options
- Traditional string representation for Hebrew years
- Improved documentation

### Changes

- `HebrewDate` and `HebrewYear` accept a formatted string for the year argument (see formats in docs)
- `HebrewDate.genesis` represents the number of **parts** since the epoch instead of days
- refactored the `with_gregorian` argument from the formatting methods of `HebrewCalendar` and `HTMLHebrewCalendar`,
  to an attribute of these classes, which can be passed upon initialization or set later.
- renamed `HebrewCalendar.itermonthdays2gregorian` to `HebrewCalendar.itermonthdays2`
- `HebrewCalendar.itermonthdays2` always yields Gregorian dates and holiday strings
  (in addition to the default day and weekday). If the corresponding flags are set to False, 
  then they are guaranteed to be empty strings.
- `HTMLHebrewCalendar.format_day` accepts additional non-keyword arguments to insert into its element

### Fixed

- Incorrect subtraction between `HebrewDate` instances
- `HebrewCalendar` didn't account for old dates, which cannot have a Gregorian date


### Removed

- Removed support for Python version 3.8
- `IllegalMonthError` and `IllegalWeekdayError`. Using standard `ValueError` instead.

## [1.0.0] - 29-04-2025

### Added

- Conversion between Hebrew and Gregorian dates.
- Computation of weekdays, month lengths, and leap years for Hebrew dates.
- Operations for date arithmetic, such as adding and subtracting days, months, and years.
- Methods for getting today's Hebrew date or constructing a Hebrew date from a Gregorian date.
- Calendar iteration and formatting for Hebrew dates in HTML format.
- Right-to-left (RTL) HTML calendar display with optional Gregorian date annotations.
- Customizable CSS styling for calendar presentation.
- Support for generating complete calendar pages for months and years.
