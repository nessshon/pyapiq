import typing as t

from aiohttp import ClientResponse, ClientSession, ClientTimeout
from aiolimiter import AsyncLimiter

from ..exceptions import RateLimitExceeded
from ..types import HTTPMethod


class AsyncRequestor:

    def __init__(
            self,
            rps: t.Optional[int] = None,
            max_retries: t.Optional[int] = None,
            **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._max_retries = max_retries
        self._limiter: t.Optional[AsyncLimiter] = (
            AsyncLimiter(rps, 1)
            if rps is not None else None
        )

    async def safe_request(
            self,
            session: ClientSession,
            method: HTTPMethod,
            url: str,
            *,
            params: t.Optional[t.Dict[str, t.Any]] = None,
            payload: t.Optional[t.Dict[str, t.Any]] = None,
            headers: t.Optional[t.Dict[str, str]] = None,
            cookies: t.Optional[t.Dict[str, str]] = None,
            timeout: t.Optional[float] = None,
    ) -> ClientResponse:
        if self._max_retries is None:
            return await self._make_request(
                session, method, url,
                params=params, payload=payload,
                headers=headers, cookies=cookies,
                timeout=timeout,
            )

        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            response = await self._make_request(
                session, method, url,
                params=params, payload=payload,
                headers=headers, cookies=cookies,
                timeout=timeout,
            )

            if response.status != 429:
                return response

            if attempt == attempts:
                raise RateLimitExceeded(url, attempt)

        raise RateLimitExceeded(url, attempts)

    async def _make_request(
            self,
            session: ClientSession,
            method: HTTPMethod,
            url: str,
            *,
            params: t.Optional[t.Dict[str, t.Any]],
            payload: t.Optional[t.Dict[str, t.Any]],
            headers: t.Optional[t.Dict[str, t.Any]],
            cookies: t.Optional[t.Dict[str, t.Any]],
            timeout: t.Optional[float],
    ) -> ClientResponse:
        if self._limiter:
            async with self._limiter:
                pass

        return await session.request(
            method,
            url,
            params=params,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=ClientTimeout(total=timeout),
        )
