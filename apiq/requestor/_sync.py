import typing as t

from ratelimiter import RateLimiter
from requests import Session, Response

from ..exceptions import RateLimitExceeded
from ..types import HTTPMethod


class SyncRequestor:

    def __init__(
            self,
            rps: t.Optional[int] = None,
            max_retries: t.Optional[int] = None,
            **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._max_retries = max_retries
        self._limiter = (
            RateLimiter(rps, 1)
            if rps is not None else None
        )

    def safe_request(
            self,
            session: Session,
            method: HTTPMethod,
            url: str,
            *,
            params: t.Optional[t.Dict[str, t.Any]] = None,
            payload: t.Optional[t.Dict[str, t.Any]] = None,
            headers: t.Optional[t.Dict[str, str]] = None,
            cookies: t.Optional[t.Dict[str, str]] = None,
            timeout: t.Optional[float] = None,
    ) -> Response:
        if self._max_retries is None:
            return self._make_request(
                session, method, url,
                params=params, payload=payload,
                headers=headers, cookies=cookies,
                timeout=timeout
            )

        attempts = self._max_retries + 1
        for attempt in range(1, attempts + 1):
            response = self._make_request(
                session, method, url,
                params=params, payload=payload,
                headers=headers, cookies=cookies,
                timeout=timeout
            )

            if response.status_code != 429:
                return response

            if attempt == attempts:
                raise RateLimitExceeded(url, attempt)

        raise RateLimitExceeded(url, attempts)

    def _make_request(
            self,
            session: Session,
            method: HTTPMethod,
            url: str,
            *,
            params: t.Optional[t.Dict[str, t.Any]],
            payload: t.Optional[t.Dict[str, t.Any]],
            headers: t.Optional[t.Dict[str, t.Any]],
            cookies: t.Optional[t.Dict[str, t.Any]],
            timeout: t.Optional[float],
    ) -> Response:
        if self._limiter:
            with self._limiter:
                pass

        return session.request(
            method,
            url,
            params=params,
            json=payload,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
        )
