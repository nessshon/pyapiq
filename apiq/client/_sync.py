from __future__ import annotations

import typing as t

import requests

from ._base import BaseClientAPI
from ..exceptions import UnsupportedResponseType
from ..parsers import ResponseParser
from ..requestor import SyncRequestor
from ..types import HTTPMethod, ReturnAs, ReturnType
from ..utils import try_parse_json


class SyncClientAPI(BaseClientAPI, SyncRequestor):
    rps: t.Optional[int] = None
    max_retries: t.Optional[int] = None

    headers: t.Optional[t.Dict[str, str]] = None
    cookies: t.Optional[t.Dict[str, str]] = None
    timeout: t.Optional[float] = None

    def __init__(
            self,
            base_url: t.Optional[str] = None,
            version: t.Optional[str] = None,
            rps: t.Optional[int] = None,
            max_retries: t.Optional[int] = None,
            *,
            session: t.Optional[requests.Session] = None,
            headers: t.Optional[dict[str, str]] = None,
            timeout: t.Optional[float] = None,
            cookies: t.Optional[dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url or self.__class__.base_url
        self.version = version or self.__class__.version

        self.rps = rps or self.__class__.rps
        self.max_retries = max_retries or self.__class__.max_retries

        super().__init__(
            base_url=self.base_url,
            version=self.version,
            rps=self.rps,
            max_retries=self.max_retries,
        )
        self.headers = headers
        self.timeout = timeout
        self.cookies = cookies

        self._session = session
        self._session_owner = session is None

    def __enter__(self) -> SyncClientAPI:
        self.ensure_session()
        return self

    def __exit__(
            self,
            exc_type: t.Optional[type[BaseException]],
            exc_value: t.Optional[BaseException],
            traceback: t.Optional[t.Any],
    ) -> None:
        self.close()

    @staticmethod
    def parse_response(
            response: requests.Response,
            *,
            return_as: ReturnAs = ReturnType.JSON,
    ) -> t.Any:
        parser = ResponseParser(return_as=return_as)
        return_type, _ = parser.detect_return_type()

        status = response.status_code
        url = response.url
        data: t.Optional[t.Union[bytes, str, t.Dict[str, t.Any]]]

        if return_type == ReturnType.RESPONSE:
            data = None
        elif return_type == ReturnType.BYTES:
            data = response.content
        elif return_type == ReturnType.TEXT:
            data = response.text
        elif return_type == ReturnType.JSON:
            try:
                data = response.json()
            except (Exception,):
                data = try_parse_json(response.text)
        else:
            raise UnsupportedResponseType(str(return_type))

        return parser.parse(
            status=status,
            url=url,
            data=data,
            raw_response=response,
        )

    def request(
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
        self.ensure_session()
        assert self._session is not None
        merged_headers = {**(self.headers or {}), **(headers or {})}
        merged_cookies = {**(self.cookies or {}), **(cookies or {})}
        merged_timeout = timeout if timeout is not None else self.timeout

        response = self.safe_request(
            self._session,
            method,
            url,
            params=params,
            payload=payload,
            headers=merged_headers,
            cookies=merged_cookies,
            timeout=merged_timeout,
        )
        return self.parse_response(response, return_as=return_as)

    def ensure_session(self) -> None:
        if self._session is None:
            self._session = requests.Session()
            if self.headers is not None:
                self._session.headers.update(self.headers)
            if self.cookies is not None:
                self._session.cookies.update(self.cookies)
            self._session_owner = True

    def close(self) -> None:
        if self._session_owner and self._session:
            self._session.close()
