# src/timesl/core/state.py

class VirtualTimeState:
    def __init__(self):
        self.active = False
        self.offset_ms = 0

    def advance(self, ms: int):
        self.offset_ms += ms


VT_STATE = VirtualTimeState()