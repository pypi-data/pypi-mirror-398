# src/timesl/clock.py

from datetime import datetime

def now():
    return datetime.now()

def format_time(fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.now().strftime(fmt)