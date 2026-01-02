# src/timesl/core/sleep.py

import time
from ..units import UNITS, DEFAULT_UNIT
from ..config import VT_THRESHOLD_UNIT, ENABLE_VT
from ..exceptions import InvalidUnitError
from .vt import vt_sleep

def sleep(value: float, unit: str = DEFAULT_UNIT):
    if unit not in UNITS:
        raise InvalidUnitError(f"Unknown time unit: {unit}")

    factor = UNITS[unit]

    # Chuyển VT
    if factor == "VT":
        if ENABLE_VT:
            vt_sleep(value)
            return
        else:
            raise RuntimeError("Virtual Time disabled")

    ms = int(value * factor)
    time.sleep(ms / 1000)