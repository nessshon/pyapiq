import abc
import typing as t

from ..client import AsyncClientAPI, SyncClientAPI


class BaseAPINamespace(abc.ABC):
    client: t.Union[AsyncClientAPI, SyncClientAPI]

    @property
    @abc.abstractmethod
    def namespace(self) -> str: ...

    def _consume_url(self, *parts: str) -> str:
        return self.client._consume_url(*parts)  # noqa

    def _resolve_url(self, *parts: str) -> str:
        return self.client._consume_url(self.namespace, *parts)  # noqa
