class APIQException(Exception):
    """
    Base exception class for all APIQ-related errors.
    """
    pass


class RateLimitExceeded(APIQException):
    """
    Raised when the request fails due to exceeding rate limits (HTTP 429).

    :param url: URL of the request that failed.
    :param attempts: Number of attempts made before giving up.
    """

    def __init__(self, url: str, attempts: int):
        super().__init__(f"Request to {url} failed after {attempts} attempts due to rate limiting (HTTP 429).")


class UnauthorizedError(APIQException):
    """
    Raised when the request is unauthorized (HTTP 401).

    :param url: URL of the unauthorized request.
    """

    def __init__(self, url: str):
        super().__init__(f"Unauthorized (HTTP 401). Check your API key or permissions for {url}.")


class HTTPClientResponseError(APIQException):
    """
    Raised when a non-OK HTTP response is received.

    :param url: URL of the failed request.
    :param status: HTTP status code returned.
    :param message: Error message or parsed content from response.
    """

    def __init__(self, url: str, status: int, message: str):
        super().__init__(f"HTTP {status} Error for {url}: {message}")


__all__ = [
    "APIQException",
    "RateLimitExceeded",
    "UnauthorizedError",
    "HTTPClientResponseError",
]
