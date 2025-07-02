from __future__ import annotations

import asyncio
import json
import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import aiohttp
from aiolimiter import AsyncLimiter

from .exceptions import (
    UnauthorizedError,
    HTTPClientResponseError,
    RateLimitExceeded,
)
from .logger import (
    setup_logger,
    log_request,
    log_response,
)


class APIClient(ABC):
    """
    Base abstract asynchronous API client with built-in rate limiting, retries,
    structured logging, and automatic JSON parsing.

    Inherit from this class to define your own API clients by implementing
    the `url` and `version` properties.
    """

    def __init__(
            self,
            headers: Optional[Dict[str, str]] = None,
            timeout: int = 10,
            rps: int = 1,
            max_retries: int = 3,
            debug: bool = False,
    ) -> None:
        """
        Initialize the API client.

        :param headers: Optional default headers for all requests.
        :param timeout: Total timeout per request in seconds.
        :param rps: Requests per second rate limit.
        :param max_retries: Maximum number of retries on failure or rate limiting.
        :param debug: If True, enables detailed debug logging.
        """
        self._headers = headers or {}
        self._timeout = timeout
        self._rps = rps
        self._max_retries = max_retries
        self._debug = debug

        self._limiter = AsyncLimiter(self._rps, 1)
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}", debug)

    @property
    def api(self) -> APIClient:
        """
        Returns self for interface consistency with APINamespace classes.

        :return: Self instance.
        """
        return self

    @property
    @abstractmethod
    def url(self) -> str:
        """
        Base URL of the API. Must be implemented by subclasses.

        :return: API base URL string.
        """
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """
        API version path segment. Must be implemented by subclasses.

        :return: API version string.
        """
        pass

    def build_url(self, *parts: str) -> str:
        """
        Safely joins base_url, version, and additional path parts into a full URL.
        Removes duplicate slashes and trailing slashes.

        :param parts: Additional path segments to append.
        :return: Fully constructed URL.
        """
        segments = [self.url.rstrip("/")]

        if self.version:
            segments.append(str(self.version).strip("/"))
        segments += [str(p).strip("/") for p in parts if p]

        return "/".join(segments)

    @staticmethod
    async def _parse_response(response: aiohttp.ClientResponse) -> Any:
        """
        Parse and return the HTTP response content as JSON if possible.

        :param response: aiohttp ClientResponse object.
        :return: Parsed JSON object or raw text if not JSON.
        """
        content_type = response.headers.get("Content-Type", "")
        raw_data = await response.read()

        if "application/json" not in content_type:
            return {"error": f"Unsupported response format. HTTP {response.status}", "content": raw_data.decode()}

        try:
            return json.loads(raw_data.decode())
        except json.JSONDecodeError:
            return raw_data.decode()

    @staticmethod
    async def _apply_retry_delay(
            response: Optional[aiohttp.ClientResponse] = None,
            default_delay: int = 1,
    ) -> None:
        """
        Wait before retrying a request, based on Retry-After header or a default delay.

        :param response: aiohttp ClientResponse object (optional).
        :param default_delay: Default delay in seconds if Retry-After is absent or invalid.
        """
        retry_after = default_delay
        if response and "Retry-After" in response.headers:
            try:
                retry_after = int(response.headers["Retry-After"])
            except (ValueError, TypeError):
                pass

        await asyncio.sleep(retry_after + random.uniform(0.2, 0.5))

    async def request(
            self,
            method: str,
            path: str,
            params: Optional[Dict[str, Any]] = None,
            body: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """
        Perform an HTTP request with retry logic, rate limiting, and automatic logging.

        :param method: HTTP method (GET, POST, etc.).
        :param path: API endpoint path or full URL.
        :param params: Query parameters dictionary.
        :param body: Request body dictionary (JSON).
        :param headers: Optional additional headers.
        :return: Parsed JSON response or raw text.
        :raises UnauthorizedError: If response status is 401.
        :raises HTTPClientResponseError: For other non-OK statuses.
        :raises RateLimitExceeded: If all retries exhausted due to rate limiting.
        """
        merged_headers = {**self._headers, **(headers or {})}
        url = path if path.startswith("http") else self.build_url(path)
        timeout = aiohttp.ClientTimeout(total=self._timeout)

        if self._debug:
            log_request(self.logger, method, url, merged_headers, params, body)

        for attempt in range(self._max_retries + 1):
            async with self._limiter:
                try:
                    async with aiohttp.ClientSession(headers=merged_headers, timeout=timeout) as session:
                        async with session.request(
                                method=method,
                                url=url,
                                params=params,
                                json=body,
                        ) as response:
                            content = await self._parse_response(response)

                            if self._debug:
                                log_response(self.logger, response.status, content)

                            if response.status == 429:
                                await self._apply_retry_delay(response)
                                continue
                            if response.status == 401:
                                raise UnauthorizedError(url)
                            if not response.ok:
                                raise HTTPClientResponseError(url, response.status, str(content))
                            return content

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.logger.error(f"[APIQ ERROR] Exception during request: {e}")
                    raise

        raise RateLimitExceeded(url, self._max_retries + 1)


__all__ = ["APIClient"]
