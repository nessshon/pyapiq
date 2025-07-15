import functools
import inspect
import typing as t

from pydantic import BaseModel

from .client import AsyncClientAPI, SyncClientAPI
from .namespace import AsyncAPINamespace, SyncAPINamespace
from .types import ReturnAs, ReturnType
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


def _build_request(
        func: t.Callable,
        sig: inspect.Signature,
        method: str,
        path: t.Optional[str],
        return_as: ReturnAs,
) -> t.Callable[..., t.Dict[str, t.Any]]:
    path_keys = extract_path_keys(path) if path else set()

    def wrapper(
            self_obj: ClientLike,
            *args: t.Any,
            **kwargs: t.Any,
    ) -> t.Dict[str, t.Any]:
        bound = sig.bind(self_obj, *args, **kwargs)
        bound.apply_defaults()
        args_dict = dict(bound.arguments)
        args_dict.pop("self", None)

        _path = path or f"/{func.__name__}"
        endpoint_path = format_path(_path, args_dict)

        if hasattr(self_obj, "_resolve_url"):
            url = self_obj._resolve_url(endpoint_path)  # noqa
        else:
            url = self_obj._consume_url(endpoint_path)  # noqa

        query_params = {
            k: v for k, v in args_dict.items()
            if k not in path_keys and k != "payload"
        }

        payload = kwargs.pop("payload", args_dict.pop("payload", None))
        if isinstance(payload, BaseModel):
            payload = payload.model_dump(mode="json")

        return dict(
            method=method,
            url=url,
            params=query_params,
            payload=payload,
            return_as=return_as,
        )

    return wrapper


def async_endpoint(
        method: str,
        *,
        path: t.Optional[str] = None,
        return_as: ReturnAs = ReturnType.JSON,
) -> t.Callable[[t.Callable[P, t.Awaitable[R]]], t.Callable[P, t.Awaitable[R]]]:
    def decorator(func: t.Callable[P, t.Awaitable[R]]) -> t.Callable[P, t.Awaitable[R]]:
        sig = inspect.signature(func)
        build_request = _build_request(func, sig, method, path, return_as)

        @functools.wraps(func)
        async def wrapper(
                self_obj: AsyncClientLike,
                *args: P.args,
                **kwargs: P.kwargs,
        ) -> R:
            req = build_request(self_obj, *args, **kwargs)
            return await self_obj.request(**req)

        return t.cast(t.Callable[P, t.Awaitable[R]], wrapper)

    return decorator


def sync_endpoint(
        method: str,
        *,
        path: t.Optional[str] = None,
        return_as: ReturnAs = ReturnType.JSON,
) -> t.Callable[[t.Callable[P, R]], t.Callable[P, R]]:
    def decorator(func: t.Callable[P, R]) -> t.Callable[P, R]:
        sig = inspect.signature(func)
        build_request = _build_request(func, sig, method, path, return_as)

        @functools.wraps(func)
        def wrapper(
                self_obj: SyncClientLike,
                *args: P.args,
                **kwargs: P.kwargs,
        ) -> R:
            req = build_request(self_obj, *args, **kwargs)
            return self_obj.request(**req)

        return t.cast(t.Callable[P, R], wrapper)

    return decorator
