"""
This module contains information about Hebrew holidays, festive days and fasting days.
"""
#  Copyright (c) 2025 Isaac Dovolsky

HOLIDAYS = {
    'תשרי': {
        'ראש השנה': (1, 2),
        'יום כיפור': 10,
        'יו"ט ראשון של סוכות': 15,
        'שמחת תורה': 22,
    },
    'ניסן': {
        'יו"ט ראשון של פסח': 15,
        'שביעי של פסח': 21
    },
    'סיוון': {
        'שבועות': 6
    }
}
FESTIVE_DAYS = {
    'תשרי': {
        'חול המועד סוכות': (16, 17, 18, 19, 20),
        'הושענא רבה': 21
    },
    'כסלו': {
        'חנוכה': (25, 26, 27, 28, 29, 30)
    },
    'טבת': {
        'חנוכה': (1, 2, 3)
    },
    'שבט': {
        'ט"ו בשבט': 15
    },
    'אדר': {
        'פורים': 14,
        'שושן פורים': 15,
        'שושן פורים משולש': 16
    },
    'ניסן': {
        'חול המועד פסח': (16, 17, 18, 19, 20)
    },
    'אייר': {
        'ל"ג בעומר': 18
    },
    'אב': {
        'ט"ו באב': 15
    }
}
FASTS = {
    'תשרי': {
        'צום גדליה': 3
    },
    'טבת': {
        'צום עשרה בטבת': 10
    },
    'אדר': {
        'תענית אסתר': 13
    },
    'תמוז': {
        'צום י"ז בתמוז': 17
    },
    'אב': {
        'צום תשעה באב': 9
    }
}
FESTIVE_DAYS['אדר ב'] = FESTIVE_DAYS['אדר']
FASTS['אדר ב'] = FASTS['אדר']

def get_holiday(date, include_festive_days: bool = False, include_fasts: bool = False) -> tuple[bool, str]:
    """Checks if the given Hebrew date is a holiday, festive day, or fast.

    Args:
        date (HebrewDate): The date to check.
        include_festive_days (bool): Whether to include festive days like Hanukkah or Chol HaMoed.
        include_fasts (bool): Whether to include fasting days.

    Returns:
        tuple[bool, str]: A tuple containing (is_holiday, holiday_name).
            If not a holiday, returns (False, '').
    """
    # Support for Adar/Adar II mapping
    day_numeric = date.day_numeric
    weekday_numeric = date.weekday_numeric

    # Check main holidays
    if date.month in HOLIDAYS:
        for holiday, day in HOLIDAYS[date.month].items():
            if isinstance(day, tuple):
                if day_numeric in day:
                    return True, holiday
            elif day_numeric == day:
                return True, holiday

    if include_festive_days:
        if date.month in FESTIVE_DAYS:
            # Check for Hanukkah length which depends on Kislev length
            if date.month == 'טבת' and day_numeric == 3:
                if date.year.days[2] == 30:
                    return False, ''
            
            if date.month in ('אדר', 'אדר ב') and day_numeric == 16:
                # Purim Meshulash: only if 15 Adar is Shabat (so 16 Adar is Sunday)
                if weekday_numeric != 1:
                    return False, ''
            
            for festive, day in FESTIVE_DAYS[date.month].items():
                if isinstance(day, (tuple, set)):
                    if day_numeric in day:
                        return True, festive
                elif day_numeric == day:
                    return True, festive

    if include_fasts:
        if date.month in FASTS:
            actual_check_day = day_numeric
            if date.month in ('אדר', 'אדר ב'):
                if day_numeric == 13 and weekday_numeric == 7:
                    return False, '' # Fast moved to Thursday
                if day_numeric == 11 and weekday_numeric == 5:
                    actual_check_day = 13
            elif date.month in ('תשרי', 'תמוז', 'אב'):
                base_day = list(FASTS[date.month].values())[0]
                if day_numeric == base_day and weekday_numeric == 7:
                    return False, '' # Fast moved to Sunday
                if day_numeric == base_day + 1 and weekday_numeric == 1:
                    actual_check_day = base_day
            
            for fast, day in FASTS[date.month].items():
                if actual_check_day == day:
                    return True, fast

    return False, ''