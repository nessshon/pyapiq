import json
import typing as t

__all__ = [
    "APIQException",
    "APIClientResponseError",
    "APIClientTypeError",
    "MissingBaseURLError",
    "RateLimitExceeded",
    "UnsupportedResponseType",
    "GETRequestPayloadError",
    "APIClientBadRequestError",
    "APIClientUnauthorizedError",
    "APIClientForbiddenError",
    "APIClientNotFoundError",
    "APIClientTooManyRequestsError",
    "APIClientServerError",
    "APIClientNotImplementedError",
    "ERROR_CLASSES",
    "ERROR_LABELS",
    "CLOUD_PROTECTION_MARKERS",
]


class APIQException(Exception):
    pass


class APIClientResponseError(APIQException):

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        url: t.Optional[str] = None,
        detail: t.Any = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.url = url
        self.detail = detail
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        phrase = ERROR_LABELS.get(self.status_code, "Unknown Error")
        parts = [f"HTTP {self.status_code} {phrase}"]
        if self.url:
            parts.append(f"url: {self.url}")
        if self.message:
            parts.append(f"message: {self.message}")
        if self.detail:
            try:
                detail_str = json.dumps(self.detail, ensure_ascii=False)
            except (Exception,):
                detail_str = repr(self.detail)
            parts.append(f"details: {detail_str}")
        return "; ".join(parts)


class APIClientTypeError(APIQException):
    def __init__(
        self,
        namespace: str,
        expected_type: type,
        received_instance: t.Any,
    ) -> None:
        message = (
            f"{namespace} requires a 'client' that is a subclass of {expected_type.__name__}, "
            f"but got {type(received_instance).__name__}, which is not."
        )
        super().__init__(message)


class MissingBaseURLError(APIQException):
    def __init__(self, cls: type) -> None:
        super().__init__(
            f"{cls.__name__} initialization failed: "
            f"'base_url' must be provided either as an argument or defined as a class attribute."
        )


class RateLimitExceeded(APIClientResponseError):
    def __init__(self, url: str, attempts: int) -> None:
        super().__init__(
            message=f"Rate limit exceeded after {attempts} attempts",
            status_code=429,
            url=url,
        )
        self.attempts = attempts


class UnsupportedResponseType(APIQException):
    def __init__(self, response_type: str) -> None:
        self.response_type = response_type
        self.message = f"Unsupported response type: '{response_type}'"
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        return f"Client Error; message: {self.message}"


class GETRequestPayloadError(APIQException):
    def __init__(self, key: str, value: t.Any) -> None:
        message = (
            f"GET method should not receive payload-like data. "
            f"Got key '{key}' with type '{type(value).__name__}' which is not allowed."
        )
        super().__init__(message)


class APIClientBadRequestError(APIClientResponseError): ...


class APIClientUnauthorizedError(APIClientResponseError): ...


class APIClientForbiddenError(APIClientResponseError): ...


class APIClientNotFoundError(APIClientResponseError): ...


class APIClientTooManyRequestsError(APIClientResponseError): ...


class APIClientServerError(APIClientResponseError): ...


class APIClientNotImplementedError(APIClientResponseError): ...


ERROR_CLASSES: t.Dict[int, type[APIClientResponseError]] = {
    400: APIClientBadRequestError,
    401: APIClientUnauthorizedError,
    403: APIClientForbiddenError,
    404: APIClientNotFoundError,
    429: APIClientTooManyRequestsError,
    500: APIClientServerError,
    501: APIClientNotImplementedError,
}

ERROR_LABELS: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}

CLOUD_PROTECTION_MARKERS: t.Dict[str, str] = {
    "cloudflare": "Cloudflare protection triggered or blocked the request.",
    "cf-ray": "Cloudflare intermediate error (cf-ray header detected).",
    "akamai": "Akamai CDN blocked or intercepted the request.",
    "fastly": "Fastly error response detected.",
    "varnish": "Varnish cache/CDN interference.",
    "nginx": "Generic reverse proxy (nginx) error response.",
    "502 bad gateway": "Bad gateway from upstream or proxy.",
    "503 service unavailable": "Service temporarily unavailable (possible proxy).",
}
