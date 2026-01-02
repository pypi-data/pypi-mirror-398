# src/timesl/calendarx.py

import calendar

def is_leap(year: int) -> bool:
    return calendar.isleap(year)

def days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]