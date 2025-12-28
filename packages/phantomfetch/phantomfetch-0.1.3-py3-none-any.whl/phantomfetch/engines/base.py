# engines/base.py
from typing import Any, Protocol

from ..types import Action, Proxy, Response


class Engine(Protocol):
    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> Response: ...


class BrowserEngine(Protocol):
    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        actions: list[Action] | None = None,
        timeout: float = 30.0,
        **kwargs: Any,
    ) -> Response: ...

    async def connect(self) -> None: ...

    async def disconnect(self) -> None: ...
