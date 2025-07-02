from abc import ABC, abstractmethod

from .client import APIClient


class APINamespace(ABC):
    """
    Base class for API namespaces/groups to structure endpoints.

    :param api: APIClient instance used for requests within this namespace.
    """

    def __init__(self, api: APIClient):
        self.api = api

    @property
    @abstractmethod
    def path(self) -> str:
        """
        Base path for this namespace.

        :return: Namespace path as string.
        """
        pass

    def build_url(self, *parts: str) -> str:
        """
        Builds full URL using APIClient.build_url with namespace's path as prefix.

        :param parts: Additional URL path parts to append.
        :return: Fully constructed URL.
        """
        return self.api.build_url(self.path, *parts)


__all__ = ["APINamespace"]
