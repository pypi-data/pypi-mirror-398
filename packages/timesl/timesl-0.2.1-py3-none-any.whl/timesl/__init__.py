# src/timesl/__init__.py

from .__version__ import __version__
from .core.sleep import sleep
from .clock import now, format_time

__all__ = [
    "sleep",
    "now",
    "format_time",
    "__version__",
]