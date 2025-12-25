import time
from typing import Any


class Timer:
    """
    Basic timer with context.

    Usage:
        with gd.Timer() as t:
            time.sleep(1.46)
        print(t.secs)  # 1.460746487020515
    """

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.secs: float = 0.0

    def __enter__(self) -> "Timer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        end_time = time.perf_counter()
        self.secs = end_time - self.start_time  # seconds
