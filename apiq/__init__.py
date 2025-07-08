from .client import APIQClient
from .decorators import (
    apiclient,
    apinamespace,
    endpoint,
)
from .session import RateLimitedSession
from .types import ResponseType

__all__ = [
    "APIQClient",
    "RateLimitedSession",
    "ResponseType",
    "apiclient",
    "apinamespace",
    "endpoint",
]

"""
APIQ Python Client

Provides core building blocks for creating fully asynchronous, rate-limited,
and strongly-typed API clients using decorators only — inheritance is optional.

Main features:
    - Simple client definition via @apiclient decorator.
    - Strong endpoint typing and auto-parsing via @endpoint.
    - Rate limiting, retries, and context management built-in.
    - Optional logical grouping of endpoints via @apinamespace.

"""
