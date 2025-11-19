from __future__ import annotations

import typing as t

from aiohttp import (
    ClientSession,
    ClientResponse,
    ClientTimeout,
)

from ._base import BaseClientAPI
from ..exceptions import UnsupportedResponseType
from ..parsers import ResponseParser
from ..requestor import AsyncRequestor
from ..types import HTTPMethod, ReturnAs, ReturnType
from ..utils import try_parse_json


class AsyncClientAPI(BaseClientAPI, AsyncRequestor):
    rps: t.Optional[int] = None
    time_period: t.Optional[float] = None
    max_retries: t.Optional[int] = None

    headers: t.Optional[t.Dict[str, str]] = None
    cookies: t.Optional[t.Dict[str, str]] = None
    timeout: t.Optional[float] = None

    def __init__(
        self,
        base_url: t.Optional[str] = None,
        version: t.Optional[str] = None,
        rps: t.Optional[int] = None,
        time_period: t.Optional[float] = None,
        max_retries: t.Optional[int] = None,
        *,
        session: t.Optional[ClientSession] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        timeout: t.Optional[float] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url or self.__class__.base_url
        self.version = version or self.__class__.version

        self.rps = rps or self.__class__.rps
        self.time_period = time_period or self.__class__.time_period
        self.max_retries = max_retries or self.__class__.max_retries

        super().__init__(
            base_url=self.base_url,
            version=self.version,
            rps=self.rps,
            time_period=self.time_period,
            max_retries=self.max_retries,
        )
        self.headers = headers or self.__class__.headers
        self.cookies = cookies or self.__class__.cookies
        self.timeout = timeout or self.__class__.timeout

        self._session = session
        self._session_owner = session is None

    @property
    def session(self) -> t.Optional[ClientSession]:
        return self._session

    async def __aenter__(self) -> AsyncClientAPI:
        await self.ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[t.Type[BaseException]],
        exc_value: t.Optional[BaseException],
        traceback: t.Optional[t.Any],
    ) -> None:
        await self.close()

    @staticmethod
    async def parse_response(
        response: ClientResponse,
        *,
        return_as: ReturnAs = ReturnType.JSON,
    ) -> t.Any:
        parser = ResponseParser(return_as=return_as)
        return_type, _ = parser.detect_return_type()

        status = response.status
        url = str(response.url)
        data: t.Optional[t.Union[ClientResponse, bytes, str, t.Dict[str, t.Any]]]

        if return_type in {ReturnType.NONE, ReturnType.TEXT}:
            data = await response.text()
        elif return_type == ReturnType.RESPONSE:
            data = response
        elif return_type == ReturnType.BYTES:
            data = await response.read()
        elif return_type == ReturnType.JSON:
            try:
                data = await response.json()
            except (Exception,):
                text = await response.text()
                data = try_parse_json(text)
        else:
            raise UnsupportedResponseType(str(return_as))

        return parser.parse(
            status=status,
            url=url,
            data=data,
            raw_response=response,
        )

    async def request(
        self,
        method: HTTPMethod,
        url: str,
        *,
        params: t.Optional[t.Dict[str, t.Any]] = None,
        payload: t.Optional[t.Dict[str, t.Any]] = None,
        return_as: ReturnAs = ReturnType.JSON,
        headers: t.Optional[t.Dict[str, str]] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        timeout: t.Optional[float] = None,
    ) -> t.Any:
        if self._session is None or self._session.closed:
            raise RuntimeError(
                "Client session is not initialized.\n"
                f"Use `async with {self.__class__.__name__}(...) as client:` "
                "or `await client.ensure_session()` before making requests."
            )

        merged_headers = {**(self.headers or {}), **(headers or {})}
        merged_cookies = {**(self.cookies or {}), **(cookies or {})}
        merged_timeout = timeout if timeout is not None else self.timeout

        response = await self.safe_request(
            self._session,
            method,
            url,
            params=params,
            payload=payload,
            headers=merged_headers,
            cookies=merged_cookies,
            timeout=merged_timeout,
        )
        return await self.parse_response(response, return_as=return_as)

    async def ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            timeout = ClientTimeout(self.timeout) if self.timeout is not None else None
            self._session = ClientSession(
                headers=self.headers,
                cookies=self.cookies,
                timeout=timeout,
            )
            self._session_owner = True

    async def close(self) -> None:
        if self._session_owner and self._session and not self._session.closed:
            await self._session.close()
