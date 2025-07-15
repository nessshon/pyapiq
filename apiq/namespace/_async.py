import abc
import typing as t

from ._base import BaseAPINamespace
from ..client import AsyncClientAPI
from ..exceptions import APIClientTypeError
from ..types import HTTPMethod, ReturnAs, ReturnType


class AsyncAPINamespace(BaseAPINamespace, abc.ABC):
    client: AsyncClientAPI
    namespace: str

    def __init__(self, client: AsyncClientAPI) -> None:
        if not isinstance(client, AsyncClientAPI):
            raise APIClientTypeError(self.__class__.__name__, AsyncClientAPI, client)
        self.client = client

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
        return await self.client.request(
            method, url,
            params=params,
            payload=payload,
            return_as=return_as,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
        )
