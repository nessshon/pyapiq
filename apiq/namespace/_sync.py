import abc
import typing as t

from ._base import BaseAPINamespace
from ..client import SyncClientAPI
from ..exceptions import APIClientTypeError
from ..types import HTTPMethod, ReturnAs, ReturnType


class SyncAPINamespace(BaseAPINamespace, abc.ABC):
    client: SyncClientAPI
    namespace: str

    def __init__(self, client: SyncClientAPI) -> None:
        if not isinstance(client, SyncClientAPI):
            raise APIClientTypeError(self.__class__.__name__, SyncClientAPI, client)
        self.client = client

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
        return self.client.request(
            method, url,
            params=params,
            payload=payload,
            return_as=return_as,
            headers=headers,
            cookies=cookies,
            timeout=timeout,
        )
