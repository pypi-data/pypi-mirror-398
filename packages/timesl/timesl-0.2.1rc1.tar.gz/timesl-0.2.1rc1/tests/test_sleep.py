# tests/test_sleep.py

import timesl as ts
import time

def test_sleep_milliseconds():
    start = time.time()
    ts.sleep(100)  # 100 ms
    end = time.time()

    assert 0.09 <= (end - start) <= 0.2


def test_sleep_seconds():
    start = time.time()
    ts.sleep(1, "s")
    end = time.time()

    assert 0.9 <= (end - start) <= 1.2


def test_invalid_unit():
    try:
        ts.sleep(1, "abc")
        assert False
    except Exception:
        assert True