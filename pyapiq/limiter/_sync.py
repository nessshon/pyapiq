from __future__ import annotations

import threading
import time
import typing as t


class SyncLimiter:

    def __init__(self, max_rate: int, time_period: float) -> None:
        self._max_calls = max_rate
        self._period = time_period
        self._lock = threading.Lock()
        self._timestamps: t.List[float] = []

    def when_ready(self) -> float:
        now = time.monotonic()
        with self._lock:
            ts = [
                timestamp
                for timestamp in self._timestamps
                if now - timestamp < self._period
            ]
            used = len(ts)
        if used < self._max_calls:
            return 0.0
        oldest = ts[0]
        wait = self._period - (now - oldest)
        return max(wait, 0.0)

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                self._timestamps = [
                    timestamp
                    for timestamp in self._timestamps
                    if now - timestamp < self._period
                ]
                if len(self._timestamps) < self._max_calls:
                    self._timestamps.append(now)
                    return
                sleep_for = self._period - (now - self._timestamps[0])
            time.sleep(max(sleep_for, 0.0))

    def __enter__(self) -> SyncLimiter:
        self.acquire()
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        pass
