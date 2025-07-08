import inspect
import typing as t

from aiohttp import ClientResponse
from pydantic import BaseModel

from .exceptions import (
    UnsupportedResponseType,
)
from .types import ResponseType

__all__ = [
    "parse_response",
    "get_param_names",
    "map_args_to_params",
    "format_path_with_params",
]


async def parse_response(
        response: ClientResponse,
        response_type: ResponseType,
        as_model: t.Optional[t.Type[BaseModel]] = None,
) -> t.Union[BaseModel, ClientResponse, str, bytes, t.Any]:
    """
    Parse an aiohttp response according to the specified response type.

    :param response: The aiohttp ClientResponse object to parse.
    :param response_type: Expected type of response content (see ResponseType).
    :param as_model: Optional Pydantic model class for validating JSON responses.
    :return: Parsed response content of the specified type.
    :raises UnsupportedResponseType: If the specified response_type is unsupported.
    """
    response.raise_for_status()
    if response_type == ResponseType.RESPONSE:
        return response
    elif response_type == ResponseType.TEXT:
        return await response.text()
    elif response_type == ResponseType.BYTES:
        return await response.read()
    elif response_type == ResponseType.JSON:
        resp_json = await response.json()
        if as_model:
            return as_model.model_validate(resp_json)
        return resp_json
    else:
        raise UnsupportedResponseType(str(response_type))


def get_param_names(func: t.Callable[..., t.Any]) -> list[str]:
    """
    Retrieve parameter names of a function, excluding 'self'.

    :param func: Function to inspect.
    :return: List of parameter names (str), excluding 'self'.
    """
    sig = inspect.signature(func)
    return [name for name in sig.parameters if name != "self"]


def map_args_to_params(
        func: t.Callable[..., t.Any],
        args: t.Tuple[t.Any, ...]
) -> t.Dict[str, t.Any]:
    """
    Map positional arguments to parameter names for the function.

    :param func: Function to map arguments for.
    :param args: Tuple of positional arguments.
    :return: Dictionary mapping parameter names to argument values.
    :raises ValueError: If too many positional arguments are provided.
    """
    param_names = get_param_names(func)
    if len(args) > len(param_names):
        raise ValueError(f"Too many positional arguments. Expected at most {len(param_names)}")

    return dict(zip(param_names, args))


def format_path_with_params(
        resolved_path: str,
        path_params: t.Dict[str, t.Any],
        kwargs: t.Dict[str, t.Any],
) -> t.Tuple[str, t.Set[str]]:
    """
    Format a URL path, substituting placeholders with parameter values.

    :param resolved_path: Path template with placeholders (e.g., "/users/{user_id}").
    :param path_params: Positional parameters mapped by name.
    :param kwargs: Keyword arguments for substitution.
    :return: Tuple of (a formatted path, set of used parameter keys).
    :raises ValueError: If a required path parameter is missing.
    """
    used_keys: t.Set[str] = set()

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
