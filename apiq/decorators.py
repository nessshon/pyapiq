import typing as t
from functools import wraps
from typing import Callable

from aiohttp import ClientTimeout
from pydantic import BaseModel

from . import utils
from .client import APIQClient
from .protocols import (
    APIQClientProtocol,
    APINamespaceProtocol,
)
from .types import ResponseType

__all__ = [
    "apiclient",
    "apinamespace",
    "endpoint",
]

P = t.ParamSpec("P")
R = t.TypeVar("R")
T = t.TypeVar("T", bound=type)


def endpoint(
        method: str,
        as_model: t.Optional[t.Type[BaseModel]] = None,
        response_type: ResponseType = ResponseType.JSON,
        *,
        path: t.Optional[str] = None,
        headers: t.Optional[dict[str, str]] = None,
        timeout: t.Optional[t.Union[int, float]] = None,
        cookies: t.Optional[dict[str, str]] = None,
) -> t.Callable[
    [t.Callable[P, t.Awaitable[R]]],
    t.Callable[P, t.Awaitable[R]]
]:
    """
    Decorator to define an asynchronous API endpoint method with automatic path formatting and response parsing.

    Handles building the endpoint path, injecting path and query parameters, passing request options,
    and parsing the response (including Pydantic validation if as_model is set).

    :param method: HTTP method to use (e.g., "GET", "POST").
    :param as_model: Optional Pydantic model class for validating JSON responses.
    :param response_type: The expected response type (see ResponseType).
    :param path: Relative path template for the endpoint (e.g., "/{user_id}").
    :param headers: Optional HTTP headers specific to this endpoint.
    :param timeout: Optional request timeout in seconds for this endpoint.
    :param cookies: Optional cookies to send with the request.
    :return: Decorated async function that performs the API call and returns the parsed result.
    :raises ValueError: If the path argument is incorrectly specified when used within a namespace.

    Example:
        from apiq import apiclient, endpoint, ResponseType
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str

        @apiclient(base_url="https://api.example.com", headers={"Authorization": "Bearer sk_test_xxx"})
        class MyClient:
            @endpoint(
                "GET",
                path="/users/{user_id}",
                as_model=User,
                response_type=ResponseType.JSON,
                timeout=10
            )
            async def get_user(self, user_id: int):
                '''Fetch a user by their unique ID.'''
    """

    def decorator(func: t.Callable[P, t.Awaitable[t.Any]]) -> t.Callable[P, t.Awaitable[R]]:
        @wraps(func)
        async def wrapper(self: APIQClientProtocol, *args: P.args, **kwargs: P.kwargs) -> R:
            body = kwargs.pop("body", None)
            path_params = utils.map_args_to_params(func, args)
            formatted_path, used_keys = utils.format_path_with_params(
                path or func.__name__, path_params, kwargs)
            query_params = {k: v for k, v in kwargs.items() if k not in used_keys}

            if not used_keys and path_params:
                query_params.update(path_params)
            url = self.consume_url(formatted_path)

            request_data = {
                "headers": headers or self.client.headers,
                "timeout": ClientTimeout(total=timeout or self.client.timeout),
                "cookies": cookies or self.client.cookies,
                "json": body.model_dump() if isinstance(body, BaseModel) else body,
                "params": query_params,
            }
            if response_type == ResponseType.STREAM:
                response = await self.client.stream(method, url, **request_data)
            else:
                response = await self.client.request(method, url, **request_data)
            parsed = await utils.parse_response(response, response_type, as_model)
            return t.cast(R, parsed)

        return t.cast(t.Callable[P, t.Awaitable[R]], wrapper)

    return decorator


def apiclient(
        *,
        base_url: str,
        version: t.Optional[str] = None,
        headers: t.Optional[t.Dict[str, str]] = None,
        timeout: t.Optional[float] = None,
        cookies: t.Optional[t.Dict[str, str]] = None,
        rps: int = 1,
        retries: int = 3,
) -> Callable[[T], t.Union[T, t.Type[APIQClientProtocol]]]:
    """
    Decorator to configure an API client class with all core settings.

    This decorator injects asynchronous context management, rate limiting, retry logic,
    and all required infrastructure to your client class.

    :param base_url: The base URL for all API requests (must start with "http" or "https").
    :param version: Optional API version string to be appended to all paths.
    :param headers: Optional default HTTP headers for every request.
    :param timeout: Optional default timeout in seconds for all requests.
    :param cookies: Optional cookies dict to send with all requests.
    :param rps: Maximum number of requests per second (rate limiting).
    :param retries: Maximum number of retries for rate-limited (429) requests.
    :return: Decorated API client class with all configuration applied.
    :raises ValueError: If base_url is invalid or missing.

    Example:
        from apiq import apiclient, endpoint, ResponseType
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str

        @apiclient(
            base_url="https://api.example.com",
            headers={"Authorization": "Bearer sk_test_xxx"},
            rps=1,
            retries=3
        )
        class MyClient:
            @endpoint(
                "GET",
                path="/users/{user_id}",
                as_model=User,
                response_type=ResponseType.JSON
            )
            async def get_user(self, user_id: int) -> User:
                '''Fetch a user by their unique ID.'''

        # Usage:
        client = MyClient()
        async with client:
            user = await client.get_user(user_id=123)

        Note:
        - You do NOT need to inherit from any base client. Just use @apiclient and @endpoint decorators.
        - All path parameters in the endpoint path (e.g. "/users/{user_id}") are automatically substituted from the method arguments.
        - The decorator takes care of response parsing and model validation for you.
        - You can freely mix and organize endpoints inside one or several classes as you see fit.
    """

    if (
            not base_url or
            not isinstance(base_url, str) or
            not base_url.startswith("http")
    ):
        raise ValueError("'base_url' must be a non-empty string starting with http(s)")

    def decorator(cls: t.Union[T, t.Type[APIQClientProtocol]]) -> t.Union[T, t.Type[APIQClientProtocol]]:
        attrs = dict(cls.__dict__)
        attrs.update(
            base_url=base_url,
            version=version,
            headers=headers,
            timeout=timeout,
            cookies=cookies,
            rps=rps,
            retries=retries,
        )
        return type(cls.__name__, (APIQClient, cls), attrs)

    return decorator


def apinamespace(
        namespace: str,
) -> Callable[[T], t.Union[T, t.Type[APINamespaceProtocol]]]:
    """
    Decorator for logical API namespaces, grouping related endpoints under a shared path prefix.

    Adds a __namespace__ attribute and utility methods to the class, making it easy to organize endpoint groups.

    :param namespace: Base path prefix for all endpoints in this namespace (e.g., "/users").
    :return: Decorated namespace class with __namespace__ attribute and consume_url utility.

    Example:
        from apiq import apiclient, apinamespace, endpoint, ResponseType
        from pydantic import BaseModel

        class User(BaseModel):
            id: int
            name: str

        @apinamespace("/users")
        class Users:
            @endpoint("GET", path="/{user_id}", as_model=User, response_type=ResponseType.JSON)
            async def get_user(self, user_id: int):
                '''Fetch user by their unique ID.'''

        @apiclient(base_url="https://api.example.com")
        class MyClient:
            @property
            def users(self) -> Users:
                return Users(self)

        # Usage:
        client = MyClient()
        async with client:
            user = await client.users.get_user(user_id=123)

        Note:
        - Namespaces help to group endpoints under a common path and logic (e.g. `/users`, `/payments`).
        - The decorated namespace class receives a reference to the parent client.
        - Use as many namespaces as your API structure requires, or just use a flat structure if preferred.
        - Inside endpoints, the namespace path is automatically prepended to the endpoint path.
    """

    def decorator(cls: T) -> t.Union[T, t.Type[APINamespaceProtocol]]:
        setattr(cls, "__namespace__", namespace)

        def consume_url(self, *parts: str) -> str:
            return self.client.consume_url(self.__namespace__, *parts)

        setattr(cls, "consume_url", consume_url)

        if "__init__" not in cls.__dict__:
            def __init__(self, client: APIQClient) -> None:
                self.client = client

            setattr(cls, "__init__", __init__)

        return cls

    return decorator
