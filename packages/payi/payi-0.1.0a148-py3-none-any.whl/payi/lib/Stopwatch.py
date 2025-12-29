import time
from typing import Optional


class Stopwatch:
    def __init__(self) -> None:
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start(self) -> None:
        self.start_time = time.perf_counter()

    def stop(self) -> None:
        self.end_time = time.perf_counter()

    def elapsed_s(self) -> float:
        if self.start_time is None:
            return 0.0 # ValueError("Stopwatch has not been started")
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time

    def elapsed_ms(self) -> float:
        return self.elapsed_s() * 1000

    def elapsed_ms_int(self) -> int:
        return int(self.elapsed_ms())
