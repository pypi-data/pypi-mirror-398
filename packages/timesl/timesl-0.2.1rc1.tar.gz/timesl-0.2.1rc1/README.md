# timesl

**timesl** is a Python library that extends `time.sleep` functionality with the following features:

- Supports multiple time units: from **nanoseconds** to **millennia**.  
- Default unit is **milliseconds (mls)**.  
- Supports **Virtual Time (VT)** for very long durations.  
- Provides utility functions: `ts.now()`, `ts.format_time()`, `is_leap()`, `days_in_month()`.

---

## Build Environment

This package was developed and published directly from an Android device.

- Device: Oppo A1K (released 2019, purchased 2021)
- Platform: Android
- Tools: Termux, Pydroid 3
- Python versions tested: 3.12, 3.13

---

## Requirements

- Python >= 3.9  
- Standard libraries: `datetime`, `calendar` (built-in)

---

## Installation

### 1. From PyPI (after release)
```bash
pip install timesl