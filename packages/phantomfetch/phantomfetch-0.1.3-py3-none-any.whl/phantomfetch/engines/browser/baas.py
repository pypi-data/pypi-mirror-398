import logging

from ...types import Action, BrowserEndpoint, Proxy, Response

logger = logging.getLogger(__name__)


class BaaSEngine:
    def __init__(
        self,
        endpoints: list[BrowserEndpoint] | None = None,
        timeout: float = 60.0,
    ):
        self.endpoints = endpoints or []
        self.timeout = timeout

    async def connect(self) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        actions: list[Action] | None = None,
        timeout: float | None = None,
        location: str | None = None,
        wait_until: str = "domcontentloaded",
    ) -> Response:
        return Response(
            url=url,
            status=0,
            body=b"",
            engine="browser",
            error="BaaSEngine not implemented yet",
        )
