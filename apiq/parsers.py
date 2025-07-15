import typing as t

from pydantic import BaseModel

from .exceptions import (
    APIClientResponseError,
    CLOUD_PROTECTION_MARKERS,
    ERROR_CLASSES,
)
from .types import ReturnAs, ReturnType

__all__ = [
    "ErrorParser",
    "ResponseParser",
]


class ErrorParser:

    @staticmethod
    def detect_gateway_error(
            content: t.Any,
            status_code: int,
            url: str,
    ) -> t.Optional[APIClientResponseError]:
        if isinstance(content, dict):
            body = " ".join(str(v).lower() for v in content.values())
        else:
            body = str(content).lower()

        for marker, message in CLOUD_PROTECTION_MARKERS.items():
            if marker in body:
                return APIClientResponseError(
                    message=message,
                    status_code=status_code,
                    url=url,
                    detail=content,
                )
        return None

    @staticmethod
    def extract_message(obj: t.Any) -> str:
        if isinstance(obj, dict):
            lowered = {k.lower(): v for k, v in obj.items()}
            for key in ("error", "message", "detail", "description"):
                if key in lowered and isinstance(lowered[key], str):
                    return lowered[key]
            string_values = [str(v) for v in obj.values() if isinstance(v, str)]
            return "; ".join(string_values) if string_values else str(obj)

        if isinstance(obj, list):
            return "; ".join(map(str, obj))
        if isinstance(obj, str):
            return obj
        return repr(obj)

    @classmethod
    def raise_for(cls, status: int, content: t.Any, url: str) -> None:
        exc = cls.detect_gateway_error(content, status, url)
        if exc:
            raise exc

        msg = cls.extract_message(content)
        exc_cls = ERROR_CLASSES.get(status, APIClientResponseError)
        raise exc_cls(msg, status_code=status, url=url, detail=content)


class ResponseParser:

    def __init__(self, return_as: ReturnAs = ReturnType.JSON) -> None:
        self.return_as = return_as

    def parse(
            self,
            *,
            status: int,
            url: str,
            data: t.Any,
            raw_response: t.Optional[t.Any] = None,
    ) -> t.Any:
        return_type, model = self.detect_return_type()

        if return_type == ReturnType.NONE:
            return None
        if return_type == ReturnType.RESPONSE:
            return raw_response

        if status >= 400:
            ErrorParser.raise_for(status, data, url)

        if model is not None:
            return self._deserialize_model(model, data)

        return data

    def detect_return_type(self) -> tuple[ReturnType, t.Optional[t.Type[t.Any]]]:
        if self.return_as is None:
            return ReturnType.NONE, None
        if isinstance(self.return_as, ReturnType):
            return self.return_as, None
        if isinstance(self.return_as, type):
            return ReturnType.JSON, self.return_as
        raise TypeError(f"Invalid 'return_as': {self.return_as!r}")

    @staticmethod
    def _deserialize_model(model: t.Type[t.Any], data: t.Any) -> t.Any:
        try:
            if issubclass(model, BaseModel):
                return model.model_validate(data)
            return model(data)
        except Exception as e:
            raise TypeError(f"Failed to cast response to {model.__name__}: {e}") from e
