# timesl

**timesl** is a Python library that extends `time.sleep` functionality with the following features:

- Supports multiple time units: from **nanoseconds** to **millennia**.  
- Default unit is **milliseconds (mls)**.  
- Supports **Virtual Time (VT)** for very long durations.  
- Provides utility functions: `ts.now()`, `ts.format_time()`, `is_leap()`, `days_in_month()`.

---

## Requirements

- Python >= 3.8  
- Standard libraries: `datetime`, `calendar` (built-in)

---

## Installation

### 1. From PyPI (after release)
```bash
pip install timesl