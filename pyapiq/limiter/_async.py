from __future__ import annotations

import asyncio
import time
import typing as t


class AsyncLimiter:

    def __init__(self, max_rate: int, time_period: float) -> None:
        self._max_rate = max_rate
        self._time_period = time_period
        self._tokens = max_rate
        self._lock = asyncio.Lock()
        self._last_refill = time.monotonic()

    async def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        if elapsed > 0:
            refill = elapsed * (self._max_rate / self._time_period)
            if refill >= 1:
                self._tokens = min(self._max_rate, self._tokens + int(refill))
                self._last_refill = now

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                await self._refill()
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
            await asyncio.sleep(self._time_period / self._max_rate)

    async def __aenter__(self) -> AsyncLimiter:
        await self.acquire()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        pass
