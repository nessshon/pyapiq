from __future__ import annotations

import typing as t

from aiohttp import ClientResponse

from .client import APIQClient
from .session import RateLimitedSession

__all__ = [
    "APIQClientProtocol",
    "APINamespaceProtocol",
]


@t.runtime_checkable
class APIQClientProtocol(t.Protocol):
    """
    Protocol for an API client with built-in rate limiting, retries, and context management.

    :cvar base_url: Base URL for the API (should start with 'http' or 'https').
    :cvar version: Optional API version string.
    :cvar headers: Optional default HTTP headers for all requests.
    :cvar timeout: Optional default timeout (in seconds) for requests.
    :cvar cookies: Optional default cookies for all requests.
    :cvar rps: Requests per second rate limit.
    :cvar retries: Maximum number of retries for failed requests (e.g., due to 429 rate limiting).
    """
    base_url: str
    version: t.Optional[str]

    headers: t.Optional[t.Dict[str, str]]
    timeout: t.Optional[float]
    cookies: t.Optional[t.Dict[str, str]]

    rps: int
    retries: int

    def __init__(self, **kwargs: t.Any) -> None: ...

    async def __aenter__(self) -> APIQClient: ...

    async def __aexit__(
            self,
            exc_type: t.Optional[type[BaseException]],
            exc: t.Optional[BaseException],
            tb: t.Optional[t.Any],
    ) -> None: ...

    @property
    def client(self) -> "APIQClientProtocol": ...

    @property
    def session(self) -> RateLimitedSession: ...

    def consume_url(self, *parts: str) -> str: ...

    async def ensure_session(self) -> None: ...

    async def request(self, method: str, url: str, **kwargs: t.Any) -> ClientResponse: ...

    async def stream(self, method: str, url: str, **kwargs: t.Any) -> ClientResponse: ...

    async def close(self) -> None: ...


@t.runtime_checkable
class APINamespaceProtocol(t.Protocol):
    """
    Protocol for all API namespaces.

    :var __namespace__: Namespace path.
    :var client: API client instance.
    :method consume_url: Build full URL using namespace and extra path.
    """
    __namespace__: str
    client: t.Union[t.Any, APIQClientProtocol]

    def __init__(self, client: t.Union[t.Any, APIQClientProtocol]) -> None: ...  # noqa: F841

    def consume_url(self, *parts: str) -> str: ...
