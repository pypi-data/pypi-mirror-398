# src/timesl/config.py

# Đơn vị mặc định: mili giây
DEFAULT_UNIT = "mls"

# Từ đơn vị này trở lên → chuyển sang Virtual Time
VT_THRESHOLD_UNIT = "d"   # ngày

# Độ chính xác tối đa (nanosecond)
MAX_PRECISION = "nns"

# Cho phép VT hay không
ENABLE_VT = True