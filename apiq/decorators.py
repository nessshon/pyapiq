import functools
import inspect
import typing as t
from enum import Enum

from pydantic import BaseModel

from .client import AsyncClientAPI, SyncClientAPI
from .exceptions import GETRequestPayloadError
from .namespace import AsyncAPINamespace, SyncAPINamespace
from .types import ReturnAs, ReturnType, RepeatQuery, HTTPMethod
from .utils import format_path, extract_path_keys

__all__ = [
    "async_endpoint",
    "sync_endpoint",
]

P = t.ParamSpec("P")
R = t.TypeVar("R")

AsyncClientLike = t.Union[AsyncClientAPI, AsyncAPINamespace]
SyncClientLike = t.Union[SyncClientAPI, SyncAPINamespace]
ClientLike = t.Union[AsyncClientAPI, AsyncAPINamespace, SyncClientAPI, SyncAPINamespace]


def _build_url(
    client: ClientLike,
    args_dict: t.Dict[str, t.Any],
    path: t.Optional[str],
    func: t.Callable[P, R],
) -> str:
    endpoint_path = format_path(path or func.__name__, args_dict)

    if hasattr(client, "_resolve_url"):
        return client._resolve_url(endpoint_path)  # noqa
    else:
        return client._consume_url(endpoint_path)  # noqa


def _extract_payload(
    args_dict: t.Dict[str, t.Any],
    method: HTTPMethod,
) -> t.Tuple[t.Dict[str, t.Any], t.Optional[dict]]:
    if method == HTTPMethod.GET:
        for key, val in args_dict.items():
            if isinstance(val, (BaseModel, dict)):
                raise GETRequestPayloadError(key, val)
        return args_dict, None

    for key in list(args_dict.keys()):
        value = args_dict[key]

        if isinstance(value, BaseModel):
            args_dict.pop(key)
            return args_dict, value.model_dump(mode="json")

        if isinstance(value, dict):
            args_dict.pop(key)
            return args_dict, value

    return args_dict, None


def _build_query_params(
    path_keys: t.Set[str],
    args_dict: t.Dict[str, t.Any],
    type_hints: t.Dict[str, t.Any],
) -> t.List[t.Tuple[str, str]]:
    query_params: t.List[t.Tuple[str, str]] = []

    for k, v in args_dict.items():
        if k in path_keys or v is None:
            continue

        if isinstance(v, Enum):
            v = v.value

        ann = type_hints.get(k)
        is_repeat = False

        if ann and t.get_origin(ann) is t.Annotated:
            _, *meta = t.get_args(ann)
            is_repeat = any(m is RepeatQuery for m in meta)

        if isinstance(v, list):
            if is_repeat:
                query_params.extend((k, str(item)) for item in v)
            else:
                query_params.append((k, ",".join(map(str, v))))
        else:
            query_params.append((k, str(v)))

    return query_params


def _build_request(
    func: t.Callable[P, R],
    sig: inspect.Signature,
    method: HTTPMethod,
    path: t.Optional[str],
    return_as: ReturnAs,
) -> t.Callable[P, t.Dict[str, t.Any]]:
    path_keys = extract_path_keys(path) if path else set()
    type_hints = t.get_type_hints(func, include_extras=True)

    def wrapper(
        *args: t.Any,
        **kwargs: t.Any,
    ) -> t.Dict[str, t.Any]:
        client: ClientLike = args[0]

        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        args_dict = dict(bound.arguments)
        args_dict.pop("self", None)

        url = _build_url(client, args_dict, path, func)
        args_dict, payload = _extract_payload(args_dict, method)
        query_params = _build_query_params(path_keys, args_dict, type_hints)

        return dict(
            method=method,
            url=url,
            params=query_params,
            payload=payload,
            return_as=return_as,
        )

    return wrapper


def async_endpoint(
    method: HTTPMethod,
    *,
    path: t.Optional[str] = None,
    return_as: ReturnAs = ReturnType.JSON,
) -> t.Callable[[t.Callable[P, t.Awaitable[R]]], t.Callable[P, t.Awaitable[R]]]:
    def decorator(func: t.Callable[P, t.Awaitable[R]]) -> t.Callable[P, t.Awaitable[R]]:
        sig = inspect.signature(func)
        build_request = _build_request(func, sig, method, path, return_as)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            client = t.cast(AsyncClientLike, args[0])
            req = build_request(*args, **kwargs)
            return await client.request(**req)

        return t.cast(t.Callable[P, t.Awaitable[R]], wrapper)

    return decorator


def sync_endpoint(
    method: HTTPMethod,
    *,
    path: t.Optional[str] = None,
    return_as: ReturnAs = ReturnType.JSON,
) -> t.Callable[[t.Callable[P, R]], t.Callable[P, R]]:
    def decorator(func: t.Callable[P, R]) -> t.Callable[P, R]:
        sig = inspect.signature(func)
        build_request = _build_request(func, sig, method, path, return_as)

        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            client = t.cast(SyncClientLike, args[0])
            req = build_request(*args, **kwargs)
            return client.request(**req)

        return t.cast(t.Callable[P, R], wrapper)

    return decorator
