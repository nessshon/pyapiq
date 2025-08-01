from __future__ import annotations

import typing as t
from enum import Enum, auto

__all__ = [
    "HTTPMethod",
    "ReturnType",
    "ReturnAs",
    "RepeatQuery",
]


class RepeatQuery: ...


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class ReturnType(str, Enum):
    RESPONSE = auto()
    BYTES = auto()
    JSON = auto()
    TEXT = auto()
    NONE = auto()


ReturnAs = t.Optional[t.Union[ReturnType, t.Type[t.Any]]]
