# src/timesl/core/vt.py

from .state import VT_STATE

def vt_sleep(ms: int):
    VT_STATE.active = True
    VT_STATE.advance(ms)