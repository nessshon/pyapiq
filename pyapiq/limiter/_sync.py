from __future__ import annotations

import threading
import time
import typing as t


class SyncLimiter:

    def __init__(self, max_rate: int, time_period: float) -> None:
        self._max_calls = max_rate
        self._period = time_period
        self._lock = threading.Lock()
        self._timestamps = []

    def __enter__(self) -> SyncLimiter:
        with self._lock:
            now = time.monotonic()
            self._timestamps = [
                ts for ts in self._timestamps if now - ts < self._period
            ]

            if len(self._timestamps) >= self._max_calls:
                sleep_for = self._period - (now - self._timestamps[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                self._timestamps = [
                    ts for ts in self._timestamps if now - ts < self._period
                ]

            self._timestamps.append(time.monotonic())
        return self

    def __exit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> bool:
        return False
