from __future__ import annotations

import typing as t

from ..exceptions import MissingBaseURLError


class BaseClientAPI:
    base_url: t.Optional[str] = None
    version: t.Optional[str] = None

    def __init__(
            self,
            base_url: t.Optional[str] = None,
            version: t.Optional[str] = None,
            **kwargs: t.Any,
    ) -> None:
        super().__init__(**kwargs)
        self.base_url = base_url or self.__class__.base_url
        self.version = version or self.__class__.version

        if self.base_url is None:
            raise MissingBaseURLError(self.__class__)

    def _consume_url(self, *parts: str) -> str:
        assert self.base_url is not None

        segments = [self.base_url.rstrip("/")]
        if self.version is not None:
            segments.append(self.version.rstrip("/"))
        segments += [str(p).strip("/") for p in parts if p]

        return "/".join(segments)
