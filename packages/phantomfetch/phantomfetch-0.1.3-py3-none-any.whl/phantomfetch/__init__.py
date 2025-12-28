from .cache import FileSystemCache
from .engines import BaaSEngine, CDPEngine, CurlEngine
from .fetch import Fetcher
from .pool import ProxyPool
from .types import (
    Action,
    ActionType,
    BrowserEndpoint,
    Cookie,
    EngineType,
    NetworkExchange,
    Proxy,
    ProxyStrategy,
    Response,
)

# Try to install uvloop if available
try:
    import uvloop

    uvloop.install()
except ImportError:
    pass


async def fetch(
    url: str,
    *,
    engine: EngineType = "curl",
    actions: list[Action | dict | str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float | None = None,
    wait_until: str = "domcontentloaded",
    cache: bool = False,
) -> Response:
    """
    One-liner fetch function.

    Args:
        url: Target URL
        engine: "curl" or "browser"
        actions: List of actions
        headers: Custom headers
        timeout: Timeout in seconds
        wait_until: Browser load state
        cache: If True, use default FileSystemCache
    """
    async with Fetcher(cache=cache) as f:
        return await f.fetch(
            url,
            engine=engine,
            actions=actions,
            headers=headers,
            timeout=timeout,
            wait_until=wait_until,
        )


# Alias for requests/httpx users
get = fetch

__all__ = [
    "Action",
    "ActionType",
    "BaaSEngine",
    "BrowserEndpoint",
    "CDPEngine",
    "Cookie",
    "CurlEngine",
    "EngineType",
    "Fetcher",
    "FileSystemCache",
    "NetworkExchange",
    "Proxy",
    "ProxyPool",
    "ProxyStrategy",
    "Response",
    "fetch",
    "get",
]
