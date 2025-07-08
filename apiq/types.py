from __future__ import annotations

from enum import Enum


class ResponseType(str, Enum):
    """
    Enumeration of supported response types for API client requests.

    Used to specify how the client should parse and return the response content.

    :cvar RESPONSE: Return the raw aiohttp.ClientResponse object.
    :cvar BYTES: Return the response body as bytes.
    :cvar JSON: Parse and return the response body as a JSON object (dict or list).
    :cvar TEXT: Return the response body as a decoded text string.
    :cvar STREAM: Stream the response data as received from the server.
    """
    RESPONSE = "response"
    BYTES = "bytes"
    JSON = "json"
    TEXT = "text"
    STREAM = "stream"
