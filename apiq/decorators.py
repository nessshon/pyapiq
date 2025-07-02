import inspect
from functools import wraps, lru_cache
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Literal,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    cast,
)

from pydantic import BaseModel

from apiq.logger import log_endpoint_call

_T = TypeVar("_T", bound=Callable[..., Awaitable[Any]])


@lru_cache
def _get_param_names(func: Callable[..., Any]) -> list[str]:
    """
    Retrieve parameter names of a function, excluding 'self'.

    :param func: Function to inspect.
    :return: List of parameter names excluding 'self'.
    """
    sig = inspect.signature(func)
    return [name for name in sig.parameters if name != "self"]


def _map_args_to_params(func: Callable[..., Any], args: Tuple[Any, ...]) -> Dict[str, Any]:
    """
    Map positional arguments to their corresponding parameter names.

    :param func: Function whose signature is used for mapping.
    :param args: Tuple of positional arguments.
    :return: Dictionary mapping parameter names to argument values.
    :raises ValueError: If too many positional arguments are provided.
    """
    param_names = _get_param_names(func)
    if len(args) > len(param_names):
        raise ValueError(f"Too many positional arguments. Expected at most {len(param_names)}")

    return dict(zip(param_names, args))


def _format_path(
        resolved_path: str,
        path_params: Dict[str, Any],
        kwargs: Dict[str, Any],
) -> Tuple[str, Set[str]]:
    """
    Format the resolved path using keyword arguments first, then positional path_params.

    :param resolved_path: Path template with placeholders.
    :param path_params: Positional parameters mapped to names.
    :param kwargs: Keyword arguments.
    :return: Tuple of formatted path and used keys set.
    :raises ValueError: If a required path parameter is missing.
    """
    used_keys: Set[str] = set()

    if "{" in resolved_path and "}" in resolved_path:
        try:
            formatted = resolved_path.format(**kwargs)
            used_keys.update(kwargs.keys())
            return formatted, used_keys
        except KeyError:
            pass
        try:
            formatted = resolved_path.format(**path_params)
            used_keys.update(path_params.keys())
            return formatted, used_keys
        except KeyError as e:
            raise ValueError(f"Missing path parameter: {e}")

    return resolved_path, used_keys


def endpoint(
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        path: Optional[str] = None,
        model: Optional[Type[BaseModel]] = None,
        headers: Optional[Dict[str, str]] = None,
) -> Callable[[_T], _T]:
    """
    Decorator to define an API endpoint method with automatic path formatting and response parsing.

    :param method: HTTP method (GET, POST, etc.).
    :param path: Optional endpoint path; defaults to function name.
    :param model: Optional Pydantic model class for response parsing.
    :param headers: Optional headers override.
    :return: Wrapped async function that performs the API request.
    """

    def decorator(func: _T) -> _T:
        @wraps(func)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            path_params = _map_args_to_params(func, args)
            body = kwargs.pop("body", None)
            if isinstance(body, BaseModel):
                body = body.model_dump()

            formatted_path, used_keys = _format_path(path or func.__name__, path_params, kwargs)
            query_params = {k: v for k, v in kwargs.items() if k not in used_keys}

            if not used_keys and path_params:
                query_params.update(path_params)

            if getattr(self.api, "_debug", False):
                log_endpoint_call(
                    self.api.logger,
                    method,
                    formatted_path,
                    model,
                    headers,
                    args,
                    kwargs,
                )

            response = await self.api.request(
                method=method,
                path=self.build_url(formatted_path),
                params=query_params,
                body=body,
                headers=headers,
            )

            return model(**response) if model else response

        return cast(_T, wrapper)

    return decorator


__all__ = ["endpoint"]
