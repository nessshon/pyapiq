from typing import Any

from aiohttp import ClientResponse, ClientSession
from aiolimiter import AsyncLimiter

from .exceptions import RateLimitExceeded

__all__ = ["RateLimitedSession"]


class RateLimitedSession(ClientSession):
    """
    aiohttp.ClientSession subclass with built-in rate limiting and automatic retry logic on HTTP 429.

    :param rps: Maximum allowed requests per second.
    :param retries: Maximum retry attempts on HTTP 429.
    :param args: Positional arguments for aiohttp.ClientSession.
    :param kwargs: Keyword arguments for aiohttp.ClientSession.
    """

    def __init__(
            self,
            *args: Any,
            rps: int = 1,
            retries: int = 3,
            **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._limiter: AsyncLimiter = AsyncLimiter(rps, 1)
        self._retries = retries

    async def request_with_retries(self, method: str, url: str, **kwargs: Any) -> ClientResponse:
        """
        Perform an HTTP request with rate limiting and automatic retries on HTTP 429.

        :param method: HTTP method (e.g., "GET", "POST").
        :param url: The full request URL.
        :param kwargs: Additional request arguments.
        :return: aiohttp.ClientResponse object.
        :raises RateLimitExceeded: If the maximum number of retries is exceeded.
        """
        for attempt in range(1, self._retries + 1):
            async with self._limiter:
                response = await super().request(method, url, **kwargs)
                if response.status == 429:
                    await response.release()
                    if attempt == self._retries:
                        break
                    continue
                return response
        raise RateLimitExceeded(url, self._retries)
