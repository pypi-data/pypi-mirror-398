#  Copyright (c) 2025 Isaac Dovolsky

import datetime as dt
from unittest import TestCase
from hebrewdate import HebrewDate, HebrewYear, HebrewCalendar, HTMLHebrewCalendar, HebrewMonth

class TestHebrewMonth(TestCase):

    def test_hebrew_month_initialization(self):
        year = HebrewYear(5785)
        month = HebrewMonth(year, 1)
        self.assertEqual(month.name, "תשרי")
        self.assertEqual(month.index, 1)
        self.assertEqual(month.length, 30)

        month_str = HebrewMonth(year, "ניסן")
        self.assertEqual(month_str.index, 7)
        self.assertEqual(month_str.name, "ניסן")

    def test_hebrew_month_invalid_initialization(self):
        year = HebrewYear(5785)
        with self.assertRaises(ValueError):
            HebrewMonth(year, 0)
        with self.assertRaises(ValueError):
            HebrewMonth(year, 13)
        with self.assertRaises(ValueError):
            HebrewMonth(year, "Invalid")
        with self.assertRaises(TypeError):
            HebrewMonth(year, None)

    def test_hebrew_month_leap_year(self):
        year = HebrewYear(5784)  # Leap year
        self.assertEqual(year.month_count, 13)
        month = HebrewMonth(year, 6)
        self.assertEqual(month.name, "אדר א")
        month2 = HebrewMonth(year, 7)
        self.assertEqual(month2.name, "אדר ב")

    def test_hebrew_month_length_variation(self):
        # Test Heshvan/Kislev variations
        year_short = HebrewYear(5784)  # Heshvan 29, Kislev 29
        self.assertEqual(HebrewMonth(year_short, 2).length, 29)
        self.assertEqual(HebrewMonth(year_short, 3).length, 29)

        year_long = HebrewYear(5785)  # Heshvan 30, Kislev 30
        self.assertEqual(HebrewMonth(year_long, 2).length, 30)
        self.assertEqual(HebrewMonth(year_long, 3).length, 30)

    def test_hebrew_month_str_repr(self):
        year = HebrewYear(5785)
        month = HebrewMonth(year, 1)
        self.assertEqual(str(month), "תשרי")
        self.assertEqual(repr(month), "HebrewMonth(תשרי, 5785)")

    def test_hebrew_month_equality(self):
        year = HebrewYear(5785)
        month = HebrewMonth(year, 1)
        self.assertEqual(month, 1)
        self.assertEqual(month, "תשרי")
        self.assertEqual(month, HebrewMonth(year, 1))
        self.assertNotEqual(month, 2)
        self.assertNotEqual(month, "ניסן")


class TestHebrewYear(TestCase):

    def test_hebrew_year_creation_invalid_value(self):
        with self.assertRaises(ValueError):
            HebrewYear(0)
        with self.assertRaises(ValueError):
            HebrewYear(10000)

    def test_is_leap_year_static_method(self):
        leap_year = 5784
        non_leap_year = 5783
        self.assertTrue(HebrewYear.is_leap_year(leap_year))
        self.assertFalse(HebrewYear.is_leap_year(non_leap_year))

    def test_leap_year_month_transitions(self):
        leap_year = HebrewDate(30, 6, 5784)  # Last day of Adar I
        next_day = leap_year + 1
        self.assertEqual(next_day.month, "אדר ב")
        self.assertEqual(next_day.day_numeric, 1)

    def test_month_count_based_on_leap_year(self):
        leap_year = HebrewYear(5784)
        non_leap_year = HebrewYear(5783)
        self.assertEqual(leap_year.month_count, 13)
        self.assertEqual(non_leap_year.month_count, 12)

    def test_days_array_length(self):
        leap_year = HebrewYear(5784)
        non_leap_year = HebrewYear(5783)
        self.assertEqual(len(leap_year.days), 13)
        self.assertEqual(len(non_leap_year.days), 12)

    def test_total_days_in_year(self):
        leap_year = HebrewYear(5784)
        non_leap_year = HebrewYear(5783)
        self.assertTrue(isinstance(leap_year.total_days(), int))
        self.assertTrue(isinstance(non_leap_year.total_days(), int))

    def test_month_dict_keys_and_values(self):
        year = HebrewYear(5783)
        months = year.month_dict()
        self.assertEqual(len(months), len(year.months))
        for month, days in months.items():
            self.assertIn(month, year.months)
            self.assertIn(days, year.days)

    def test_new_moons_structure(self):
        year = HebrewYear(5783)
        new_moons = year.new_moons()
        self.assertEqual(len(new_moons), len(year.months))
        for month, time in new_moons.items():
            self.assertIn(month, year.months)
            self.assertTrue(isinstance(time, str))
            self.assertRegex(time, r'^\d:\d{1,2}:\d{1,4}$')

    def test_comparison_operations_between_two_years(self):
        year_1 = HebrewYear(5783)
        year_2 = HebrewYear(5784)
        self.assertTrue(year_1 < year_2)
        self.assertTrue(year_2 > year_1)
        self.assertTrue(year_1 != year_2)
        self.assertTrue(year_1 == HebrewYear(5783))

    def test_arithmetic_operations_year_addition(self):
        year = HebrewYear(5783)
        new_year = year + 1
        self.assertEqual(new_year.year, 5784)

    def test_arithmetic_operations_year_subtraction(self):
        year = HebrewYear(5783)
        previous_year = year - 1
        year_difference = year - HebrewYear(5781)
        self.assertEqual(previous_year.year, 5782)
        self.assertEqual(year_difference, 2)

    def test_first_new_moon_result(self):
        year = HebrewYear(5783)
        first_new_moon = year.first_new_moon()
        self.assertTrue(isinstance(first_new_moon, int))
        self.assertGreater(first_new_moon, 0)

    def test_str_and_repr_methods(self):
        year = HebrewYear(5783)
        self.assertEqual(str(year), "ה'תשפ\"ג")
        self.assertEqual(repr(year), "Year(ה'תשפ\"ג)")

    def test_first_weekday_calculation(self):
        year = HebrewYear(5783)
        self.assertTrue(isinstance(year.first_weekday, int))
        self.assertIn(year.first_weekday, range(0, 7))

    def test_hebrew_year_creation_extreme_values(self):
        self.assertEqual(HebrewYear(1).year, 1)
        self.assertEqual(HebrewYear(9999).year, 9999)
        with self.assertRaises(ValueError):
            HebrewYear(10000)

    def test_year_string_parsing_comprehensive(self):
        tests = [
            ("ה'תשפ\"ה", 5785),
            ("ה תשפ\"ה", 5785),
            ("ה תשפה", 5785),
            ("ה'תשפה", 5785),
            ("א'תס\"ב", 1462),
            ("ה'תשכ\"ד", 5724),
            ("ה'תנ\"ה", 5455),
            ("א'", 1000),
            ("תשפ\"ה", 785),
        ]
        for year_str, expected in tests:
            with self.subTest(year_str=year_str):
                self.assertEqual(HebrewYear(year_str).year, expected)

    def test_year_to_str_comprehensive(self):
        tests = [
            (5785, "ה'תשפ\"ה"),
            (1462, "א'תס\"ב"),
            (5724, "ה'תשכ\"ד"),
            (5455, "ה'תנ\"ה"),
            (1000, "א'"),
            (785, "תשפ\"ה"),
            (5015, "ה'ט\"ו"),
            (5016, "ה'ט\"ז"),
        ]
        for year, expected in tests:
            with self.subTest(year=year):
                self.assertEqual(HebrewYear.year_to_str(year), expected)


class TestHebrewDate(TestCase):

    def test_hebrew_date_initialization(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        self.assertEqual(hebrew_date.day_numeric, 1)
        self.assertEqual(hebrew_date.month_numeric, 1)
        self.assertEqual(hebrew_date.year_numeric, 5785)
        with self.assertRaises(ValueError):
            HebrewDate(1, 1, "invalid")
        with self.assertRaises(ValueError):
            HebrewDate(1, 13, 5785)
        with self.assertRaises(ValueError):
            HebrewDate(32, 1, 5785)
        with self.assertRaises(ValueError):
            HebrewDate(1, "invalid", 5785)
        with self.assertRaises(ValueError):
            HebrewDate(1, 1)

    def test_hebrew_date_repr(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        self.assertTrue(isinstance(repr(hebrew_date), str))

    def test_hebrew_date_str(self):
        hebrew_date = HebrewDate(1, "תשרי", 5785)
        self.assertTrue(isinstance(str(hebrew_date), str))

    def test_hebrew_date_to_int(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        self.assertTrue(isinstance(int(hebrew_date), int))

    def test_comparison_operations(self):
        hebrew_date1 = HebrewDate(1, 1, 5785)
        hebrew_date2 = HebrewDate(2, 1, 5785)
        hebrew_date3 = HebrewDate(1, 1, 5785)
        self.assertTrue(hebrew_date1 < hebrew_date2)
        self.assertTrue(hebrew_date1 <= hebrew_date2)
        self.assertTrue(hebrew_date2 > hebrew_date1)
        self.assertTrue(hebrew_date2 >= hebrew_date1)
        self.assertTrue(hebrew_date1 != hebrew_date2)
        self.assertTrue(hebrew_date1 == hebrew_date3)

    def test_addition_operation(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        result_date = hebrew_date + 1
        self.assertEqual(result_date.day_numeric, 2)

    def test_subtraction_operation_with_int(self):
        hebrew_date = HebrewDate(2, 1, 5785)
        result_date = hebrew_date - 1
        self.assertEqual(result_date.day_numeric, 1)

    def test_subtraction_operation_with_other_hebrew_date(self):
        hebrew_date1 = HebrewDate(2, 1, 5785)
        hebrew_date2 = HebrewDate(1, 1, 5785)
        difference = hebrew_date1 - hebrew_date2
        self.assertEqual(difference, 1)

    def test_get_month(self):
        hebrew_date = HebrewDate(1, "ניסן", 5785)
        month_numeric, month_name = hebrew_date.get_month_tuple()
        self.assertEqual(month_numeric, 7)
        self.assertEqual(month_name, "ניסן")

    def test_get_day(self):
        hebrew_date = HebrewDate(3, "ניסן", 5785)
        day_numeric, day_name = hebrew_date.get_day_tuple()
        self.assertEqual(day_numeric, 3)
        self.assertTrue(isinstance(day_name, str))

    def test_get_weekday(self):
        hebrew_date = HebrewDate(1, "ניסן", 5785)
        weekday_numeric, weekday_name = hebrew_date.get_weekday_tuple()
        self.assertTrue(0 <= weekday_numeric <= 6)
        self.assertTrue(isinstance(weekday_name, str))

    def test_days_before(self):
        hebrew_date = HebrewDate(15, "תשרי", 5785)
        days_before = hebrew_date.days_before()
        self.assertTrue(isinstance(days_before, int))

    def test_days_after(self):
        hebrew_date = HebrewDate(15, "תשרי", 5785)
        days_after = hebrew_date.days_after()
        self.assertTrue(isinstance(days_after, int))

    def test_delta_method(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        result_date = hebrew_date.delta(days=1, months=1, years=1)
        self.assertTrue(isinstance(result_date, HebrewDate))
        self.assertNotEqual(result_date.year_numeric, hebrew_date.year_numeric)

    def test_delta_method_with_negative_values(self):
        hebrew_date = HebrewDate(1, 1, 5785)
        result_date = hebrew_date.delta(days=-1, months=-1, years=-1)
        self.assertTrue(isinstance(result_date, HebrewDate))
        self.assertNotEqual(result_date.year_numeric, hebrew_date.year_numeric)

    def test_from_gregorian(self):
        hebrew_date = HebrewDate.from_gregorian(day=1, month=1, year=2024)
        self.assertTrue(isinstance(hebrew_date, HebrewDate))
        with self.assertWarns(RuntimeWarning) as w:
            HebrewDate.from_gregorian(day=1, month=1, year=1)
        self.assertEqual(str(w.warning), "Hebrew dates may be inaccurate for years earlier than 1752.")

    def test_to_gregorian(self):
        hebrew_date_valid = HebrewDate(1, 1, 5785)
        hebrew_date_warn = HebrewDate(1, 1, 5000)
        hebrew_date_invalid = HebrewDate(1, 1, 2000)
        gregorian_date_valid = hebrew_date_valid.to_gregorian()
        self.assertTrue(isinstance(gregorian_date_valid, dt.date))
        with self.assertWarns(RuntimeWarning) as w:
            hebrew_date_warn.to_gregorian()
        self.assertEqual(str(w.warning), "Hebrew dates may be inaccurate for years earlier than 1752.")
        with self.assertWarns(RuntimeWarning) as w:
            hebrew_date_invalid.to_gregorian()
        self.assertEqual(str(w.warning), "The Hebrew date is too far in the past to convert to a Gregorian date.")

    def test_today_method(self):
        hebrew_date = HebrewDate.today()
        self.assertTrue(isinstance(hebrew_date, HebrewDate))

    def test_holiday_comprehensive(self):
        tests = [
            (1, 1, 5785, 'ראש השנה'),
            (2, 1, 5785, 'ראש השנה'),
            (10, 1, 5785, 'יום כיפור'),
            (15, 1, 5785, 'יו"ט ראשון של סוכות'),
            (22, 1, 5785, 'שמחת תורה'),
            (25, 3, 5785, 'חנוכה'),
            (2, 4, 5785, 'חנוכה'),
            (14, 7, 5784, 'פורים'),
            (15, 7, 5784, 'שושן פורים'),
            (15, 7, 5785, 'יו"ט ראשון של פסח'),
            (21, 7, 5785, 'שביעי של פסח'),
            (6, 9, 5785, 'שבועות'),
        ]
        for d, m, y, expected in tests:
            with self.subTest(date=(d, m, y)):
                date = HebrewDate(d, m, y, include_festive_days=True)
                self.assertEqual(date.holiday, expected)

    def test_fast_days(self):
        tests = [
            (4, 1, 5785, 'צום גדליה'), # 3 Tishrei is Shabbat, moved to 4
            (10, 4, 5785, 'צום עשרה בטבת'),
            (11, 7, 5784, 'תענית אסתר'),
            (17, 10, 5785, 'צום י"ז בתמוז'), # Sunday
            (9, 11, 5785, 'צום תשעה באב'), # Sunday
        ]
        for d, m, y, expected in tests:
            with self.subTest(date=(d, m, y)):
                date = HebrewDate(d, m, y, include_fasts=True)
                self.assertEqual(date.holiday, expected)

    def test_purim_meshulash(self):
        # In 5781, Purim in Jerusalem was Meshulash
        # 14 Adar = Friday
        # 15 Adar = Shabat (Shushan Purim)
        # 16 Adar = Sunday (Purim Meshulash)
        date = HebrewDate(16, "אדר", 5781, include_festive_days=True)
        self.assertEqual(date.holiday, "שושן פורים משולש")
        self.assertEqual(date.weekday, "ראשון")

    def test_hanukkah_length(self):
        # Test Hanukkah in a year where Kislev has 29 days (e.g. 5784)
        year_29 = HebrewYear(5784)
        self.assertEqual(year_29.days[2], 29)
        # Hanukkah: 25 Kislev to 3 Tevet (8 days)
        last_day_kislev = HebrewDate(29, 3, 5784, include_festive_days=True)
        self.assertEqual(last_day_kislev.holiday, "חנוכה")
        third_day_tevet = HebrewDate(3, 4, 5784, include_festive_days=True)
        self.assertEqual(third_day_tevet.holiday, "חנוכה")
        fourth_day_tevet = HebrewDate(4, 4, 5784, include_festive_days=True)
        self.assertEqual(fourth_day_tevet.holiday, "")

        # Test Hanukkah in a year where Kislev has 30 days (e.g. 5785)
        year_30 = HebrewYear(5785)
        self.assertEqual(year_30.days[2], 30)
        # Hanukkah: 25 Kislev to 3 Tevet (8 days)
        thirtieth_kislev = HebrewDate(30, 3, 5785, include_festive_days=True)
        self.assertEqual(thirtieth_kislev.holiday, "חנוכה")
        third_day_tevet_30 = HebrewDate(3, 4, 5785, include_festive_days=True)
        self.assertEqual(third_day_tevet_30.holiday, "")

    def test_delta_large_values(self):
        date = HebrewDate(1, 1, 5785)
        self.assertEqual(date.delta(years=1000).year_numeric, 6785)
        self.assertEqual(date.delta(years=-1000).year_numeric, 4785)
        self.assertEqual(date.delta(days=10000).year_numeric > 5785, True)
        
    def test_from_gregorian_boundary(self):
        # 1752-01-01 is the boundary
        date = dt.date(1752, 1, 1)
        h_date = HebrewDate.from_gregorian(date=date)
        self.assertEqual(h_date.to_gregorian(), date)
        
        # Test a very old date (proleptic Gregorian)
        # 1-01-01
        old_date = dt.date(1, 1, 1)
        with self.assertWarns(RuntimeWarning):
            h_date = HebrewDate.from_gregorian(date=old_date)
            # Round trip might not be perfect for very old dates due to calendar shifts,
            # but it should be consistent within our logic.
            self.assertEqual(h_date.to_gregorian(), old_date)

    def test_hebrew_date_string_parsing(self):
        date_str = "ט\"ו ניסן ה'תשפ\"ה"
        hebrew_date = HebrewDate(*date_str.split(' '))
        self.assertEqual(hebrew_date.day_numeric, 15)
        self.assertEqual(hebrew_date.month_numeric, 7)
        self.assertEqual(hebrew_date.year_numeric, 5785)

    def test_date_format_validation(self):
        with self.assertRaises(ValueError):
            HebrewDate(32, 1, 5785)  # Invalid day
        with self.assertRaises(ValueError):
            HebrewDate(1, 13, 5783)  # Invalid month for non-leap year
        with self.assertRaises(ValueError):
            HebrewDate("invalid", 1, 5785)  # Invalid string

    def test_invalid_month_values(self):
        with self.assertRaises(ValueError):
            HebrewDate(day=1, month=13, year=5785)  # Invalid in non-leap year
        with self.assertRaises(ValueError):
            HebrewDate(day=1, month="invalid", year=5785)  # Invalid month name

    def test_edge_case_dates(self):
        # Last day of the year
        last_day = HebrewDate(29, 12, 5785)
        self.assertEqual((last_day + 1).year_numeric, 5786)
        # First day of the year
        first_day = HebrewDate(1, 1, 5785)
        self.assertEqual((first_day - 1).year_numeric, 5784)

    def test_delta_edge_cases(self):
        date = HebrewDate(1, 1, 5785)
        # Test month overflow
        self.assertEqual(date.delta(months=12).month_numeric, 1)
        # Test month underflow
        self.assertEqual(date.delta(months=-1).year_numeric, 5784)
        # Test large day differences
        self.assertEqual(date.delta(days=400).year_numeric, 5786)

    def test_gregorian_conversion_roundtrip(self):
        original = HebrewDate(15, 1, 5785)
        gregorian = original.to_gregorian()
        converted = HebrewDate.from_gregorian(date=gregorian)
        self.assertEqual(original, converted)


class TestHebrewCalendar(TestCase):

    def test_itermonthdays_produces_correct_day_numbers(self):
        calendar = HebrewCalendar(firstweekday=0)
        year = 5785
        month = 1  # Assuming the first Hebrew month
        days = list(calendar.itermonthdays(year, month))
        self.assertTrue(all(isinstance(day, int) for day in days))
        self.assertEqual(days.count(0), days[0:(7 - days[0] % 7)].count(0))

    def test_itermonthdays_include_zeros_correctly(self):
        calendar = HebrewCalendar()
        year = 5785
        month = 2
        days = list(calendar.itermonthdays(year, month))
        self.assertIn(0, days)  # Ensure zeros are included before and after the month's days

    # noinspection PyTypeChecker
    def test_itermonthdays2_returns_correct_tuple_format(self):
        calendar = HebrewCalendar(with_gregorian=False, with_holidays=False)
        days = list(calendar.itermonthdays2(5785, 1))
        self.assertTrue(all(len(day_tuple) == 4 for day_tuple in days))
        self.assertTrue(all(isinstance(day_tuple[0], int) for day_tuple in days))
        self.assertTrue(all(isinstance(day_tuple[1], int) for day_tuple in days))
        self.assertTrue(all(isinstance(day_tuple[2], str) or day_tuple[2] == "" for day_tuple in days))
        self.assertTrue(all(isinstance(day_tuple[3], str) or day_tuple[3] == "" for day_tuple in days))

    def test_monthdays2calendar_returns_correct_matrix_size(self):
        calendar = HebrewCalendar()
        year = 5785
        month = 1
        matrix = calendar.monthdays2calendar(year, month)
        self.assertTrue(all(len(week) == 7 for week in matrix))
        self.assertEqual(len(matrix) * 7, len([day for week in matrix for day in week]))

    def test_monthdays2calendar_with_gregorian_flag(self):
        calendar = HebrewCalendar(with_gregorian=True)
        matrix_with_gregorian = calendar.monthdays2calendar(5785, 1)
        self.assertTrue(all(len(week) == 7 for week in matrix_with_gregorian))
        self.assertTrue(all(len(day_tuple) == 4 for week in matrix_with_gregorian for day_tuple in week))

class TestHTMLHebrewCalendar(TestCase):

    def test_calendar_boundary_gregorian(self):
        # 18 Tevet 3761 is 0001-01-01
        cal = HTMLHebrewCalendar(with_gregorian=True)
        # Suppress warnings for testing
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            html = cal.formatmonth(3761, 4)
        self.assertIn('January 1', html)
        self.assertIn('יח<br>01', html)
        self.assertIn('יז</div>', html) # No Gregorian for 17 Tevet

    def test_formatmonth_with_hebrew_year(self):
        calendar = HTMLHebrewCalendar(firstweekday=0)
        result = calendar.formatmonth(5785, 1)
        self.assertIn('<table dir="rtl', result)
        self.assertIn('תשרי ה\'תשפ"ה', result)

    def test_formatmonth_with_gregorian_dates(self):
        calendar = HTMLHebrewCalendar(firstweekday=0, with_gregorian=True)
        result = calendar.formatmonth(5785, 1)
        self.assertIn('October-November', result)

    def test_custom_data_styling(self):
        calendar = HTMLHebrewCalendar(firstweekday=0)
        calendar.custom_data = {
            15: {
                'classes': ['highlight', 'special-day'],
                'content': ['Meeting']
            }
        }
        result = calendar.formatmonth(5785, 1)
        self.assertIn('class="sat day highlight special-day"', result)
        self.assertIn('Meeting', result)

    def test_custom_data_validation(self):
        cal = HTMLHebrewCalendar()
        cal.custom_data = {
            0: {'classes': ['test']},  # Invalid day
            32: {'content': ['test']}  # Invalid day
        }
        html = cal.formatmonth(5785, 1)
        self.assertNotIn('test', html)

    def test_formatday_outside_month(self):
        calendar = HTMLHebrewCalendar(firstweekday=0)
        result = calendar.formatday(0, 0)
        self.assertEqual(result, '<td class="noday">&nbsp;</td>')

    def test_formatmonth_with_holidays(self):
        """Test holiday formatting in the calendar."""
        cal = HTMLHebrewCalendar(with_holidays=True)
        html = cal.formatmonth(5785, 1)  # Tishrei
        self.assertIn('ראש השנה', html)  # Should contain Rosh Hashana

    def test_calendar_holiday_integration(self):
        cal = HTMLHebrewCalendar(with_holidays=True, with_festive_days=True)
        date = HebrewDate(15, "ניסן", 5785)  # First day of Pesach
        self.assertTrue(date.is_holiday)
        html = cal.formatmonth(5785, date.month_numeric)
        self.assertIn(date.holiday, html)