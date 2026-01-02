# src/timesl/exceptions.py

class TimeSLException(Exception):
    """Base exception for timesl"""
    pass


class InvalidUnitError(TimeSLException):
    pass


class VirtualTimeRequired(TimeSLException):
    pass