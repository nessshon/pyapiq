from __future__ import annotations

import typing as t

from aiohttp import ClientResponse

from .session import RateLimitedSession

__all__ = ["APIQClient"]


class APIQClient:
    """
    Core class for asynchronous API clients with rate limiting, retries, and context management.

    Provides base logic for:
        - Asynchronous context management.
        - Rate limiting and retry on errors.
        - Session lifecycle and safe closing.
        - URL building and versioning.
        - Access to session and client parameters.

    :cvar base_url: Base URL for all API requests (required, must start with "http" or "https").
    :cvar version: Optional API version string appended to each request.
    :cvar headers: Optional HTTP headers used for every request.
    :cvar timeout: Optional request timeout in seconds for all requests.
    :cvar cookies: Optional cookies dict to send with every request.
    :cvar rps: Requests per second rate limit.
    :cvar retries: Maximum retry attempts for failed (429) requests.
    :ivar _session: Internal RateLimitedSession (aiohttp-based).

    :raises RuntimeError: If the client is not configured via the @apiclient decorator.
    """

    base_url: str
    version: t.Optional[str] = None

    headers: t.Optional[t.Dict[str, str]] = None
    timeout: t.Optional[float] = None
    cookies: t.Optional[t.Dict[str, str]] = None

    rps: int
    retries: int

    def __init__(self, **kwargs: t.Any) -> None:
        if not getattr(self, "base_url", None):
            raise RuntimeError(
                f"{self.__class__.__name__} is not configured! "
                f"Did you forget to use the @apiclient decorator? "
                f"Define @apiclient(base_url=...) above your client class."
            )
        for attr, val in kwargs.items():
            setattr(self, attr, val)
        self._session: t.Optional[RateLimitedSession] = None

    async def __aenter__(self) -> APIQClient:
        """
        Initialize and return the client for async context management.

        :return: The initialized APIQClient instance.
        """
        await self.ensure_session()
        return self

    async def __aexit__(
            self,
            exc_type: t.Optional[type[BaseException]],
            exc: t.Optional[BaseException],
            tb: t.Optional[t.Any],
    ) -> None:
        """
        Finalize and clean up resources when exiting the async context.

        :param exc_type: Type of exception, if any.
        :param exc: Exception instance, if any.
        :param tb: Traceback, if an exception occurred.
        :return: None
        """
        await self.close()

    @property
    def client(self) -> APIQClient:
        """
        Reference to the client instance (self).

        :return: The current APIQClient instance.
        """
        return self

    @property
    def session(self) -> RateLimitedSession:
        """
        Access the underlying RateLimitedSession.

        :return: The RateLimitedSession instance.
        :raises RuntimeError: If the session is not initialized.
        """
        if self._session is None:
            raise RuntimeError(
                "Session is not initialized. "
                "Use 'async with', or call 'await init_session()' before making requests."
            )
        return self._session

    def consume_url(self, *parts: str) -> str:
        """
        Build a full API URL from base URL, version, and additional path segments.

        :param parts: Additional URL path segments.
        :return: The full constructed API URL.
        """
        segments = [self.base_url.rstrip("/")]
        if self.version:
            segments.append(str(self.version).strip("/"))
        segments += [str(p).strip("/") for p in parts if p]
        return "/".join(segments)

    async def ensure_session(self) -> None:
        """
        Initialize the internal RateLimitedSession if not already present.

        :return: None
        """
        if self._session is None:
            self._session = RateLimitedSession(
                rps=self.rps,
                retries=self.retries,
            )

    async def request(self, method: str, url: str, **kwargs: t.Any) -> ClientResponse:
        """
        Perform an HTTP request with rate limiting and retry logic.

        :param method: HTTP method ("GET", "POST", etc).
        :param url: Full URL for the request.
        :param kwargs: Additional request parameters.
        :return: aiohttp.ClientResponse object.
        """
        await self.ensure_session()
        return await self.session.request_with_retries(method, url, **kwargs)

    async def stream(self, method: str, url: str, **kwargs: t.Any) -> ClientResponse:
        """
        Perform an HTTP request and return a streamable response.

        :param method: HTTP method.
        :param url: Full request URL.
        :param kwargs: Additional request parameters.
        :return: aiohttp.ClientResponse (streamable).
        """
        await self.ensure_session()
        return await self.session.request(method, url, **kwargs)

    async def close(self) -> None:
        """
        Closes the session and releases all resources.

        :return: None
        """
        if self._session is not None:
            await self._session.close()
            self._session = None
