__all__ = [
    "APIQException",
    "RateLimitExceeded",
    "UnsupportedResponseType",
]


class APIQException(Exception):
    """
    Base exception for all APIQ-related errors.

    All custom exceptions in the APIQ client library should inherit from this class.
    """


class RateLimitExceeded(APIQException):
    """
    Exception raised when a request exceeds the allowed rate limit (HTTP 429).

    :param url: The URL where the rate limit was exceeded.
    :param attempts: The number of retry attempts performed.
    """

    def __init__(self, url: str, attempts: int):
        super().__init__(
            f"Request to {url} failed after {attempts} attempts due to rate limiting (HTTP 429)."
        )
        self.url = url
        self.attempts = attempts


class UnsupportedResponseType(APIQException):
    """
    Exception raised when an unsupported response type is encountered.

    :param response_type: The unsupported response type.
    """

    def __init__(self, response_type: str):
        super().__init__(f"Unsupported response type from {response_type}")
        self.response_type = response_type
