# src/timesl/units.py

# Tất cả quy đổi về mili giây
UNITS = {
    # nhỏ
    "nns": 1e-6,        # nanosecond
    "mcs": 1e-3,        # microsecond
    "mls": 1,           # millisecond (mặc định)

    # lớn
    "s":   1000,
    "mn":  60_000,
    "h":   3_600_000,
    "d":   86_400_000,

    # rất lớn (chuyển VT)
    "m":   "VT",   # tháng
    "y":   "VT",   # năm
    "dc":  "VT",   # thập kỷ
    "ct":  "VT",   # thế kỷ
    "mlm": "VT",   # thiên niên kỷ
}

DEFAULT_UNIT = "mls"