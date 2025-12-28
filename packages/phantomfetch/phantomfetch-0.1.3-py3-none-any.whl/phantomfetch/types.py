from enum import Enum
from typing import Annotated, Any, Literal

import msgspec
from rusticsoup import WebPage

EngineType = Literal["curl", "browser", "auto"]
ProxyStrategy = Literal["round_robin", "random", "sticky", "geo_match", "failover"]
CacheStrategy = Literal["all", "resources", "conservative"]

ActionTypeLiteral = Literal[
    "wait",
    "click",
    "input",
    "scroll",
    "select",
    "hover",
    "screenshot",
    "wait_for_load",
    "evaluate",
    "solve_captcha",
]


class ActionType(str, Enum):
    WAIT = "wait"
    CLICK = "click"
    INPUT = "input"
    SCROLL = "scroll"
    SELECT = "select"
    HOVER = "hover"
    SCREENSHOT = "screenshot"
    WAIT_FOR_LOAD = "wait_for_load"
    EVALUATE = "evaluate"
    SOLVE_CAPTCHA = "solve_captcha"


class Proxy(msgspec.Struct):
    """
    Proxy configuration.

    Attributes:
        url: Proxy URL (e.g., http://user:pass@host:port)
        location: ISO country code (e.g., "US", "DE")
        provider: Optional provider name
        weight: Selection weight (higher = more likely to be chosen)
    """

    url: str
    location: str | None = None
    provider: str | None = None
    weight: int = 1
    failures: int = 0
    last_used: float = 0.0


class BrowserEndpoint(msgspec.Struct):
    """
    Browser-as-a-Service endpoint configuration.

    Attributes:
        url: API endpoint URL
        api_key: Optional authentication token
        max_concurrent: Max concurrent requests for this endpoint
        location: ISO country code
    """

    url: str
    api_key: str | None = None
    max_concurrent: int = 10
    location: str | None = None


class Action(msgspec.Struct):
    """
    Browser interaction definition.

    Attributes:
        action: Type of action (click, input, wait, etc.)
        selector: CSS selector to target
        value: Input value or file path
        timeout: Action timeout in ms
        api_key: API key for CAPTCHA solver (optional)
        provider: CAPTCHA provider name (optional)
        if_selector: Selector to check before executing (optional)
        if_selector_timeout: Timeout to wait for if_selector (optional)
        state: State to wait for ("visible", "attached", etc.) (optional)
        x: X coordinate for scroll (optional)
        y: Y coordinate for scroll (optional)
    """

    action: ActionType
    selector: str | None = None
    if_selector: str | None = None
    if_selector_timeout: int = 0
    value: str | int | None = None
    # Validate timeout is non-negative
    timeout: Annotated[int, msgspec.Meta(ge=0)] = 30000
    api_key: str | None = None
    provider: str | None = None
    state: str | None = None
    x: int | None = None
    y: int | None = None


class ActionResult(msgspec.Struct):
    """
    Result of a single browser action.
    """

    action: Action
    success: bool
    error: str | None = None
    data: Any = None
    duration: float = 0.0


class NetworkExchange(msgspec.Struct):
    """
    Captured network request/response details.

    Attributes:
        url: Request URL
        method: HTTP method (GET, POST, etc.)
        status: HTTP status code
        resource_type: Resource type (xhr, fetch, etc.)
        request_headers: Request headers
        response_headers: Response headers
        request_body: Request body (string if decodable)
        response_body: Response body (string if decodable)
        duration: Duration in seconds
    """

    url: str
    method: str
    status: int
    resource_type: str
    request_headers: dict[str, str]
    response_headers: dict[str, str]
    request_body: str | None = None
    response_body: str | None = None
    duration: float = 0.0


class Cookie(msgspec.Struct):
    """
    Cookie definition.

    Attributes:
        name: Cookie name
        value: Cookie value
        domain: Domain the cookie belongs to
        path: Path the cookie belongs to
        expires: Expiration timestamp
        http_only: HttpOnly flag
        secure: Secure flag
        same_site: SameSite attribute
    """

    name: str
    value: str
    domain: str | None = None
    path: str | None = None
    expires: float | None = None
    http_only: bool = False
    secure: bool = False
    same_site: Literal["Strict", "Lax", "None"] | None = None


class Response(msgspec.Struct):
    """
    Unified response object.

    Attributes:
        url: Final URL after redirects
        status: HTTP status code
        body: Response body bytes
        headers: Response headers
        engine: Engine used (curl/browser)
        elapsed: Time taken in seconds
        proxy_used: Proxy URL if used
        error: Error message if failed
        screenshot: Screenshot bytes (browser only)
        action_results: Results of executed actions (browser only)
        network_log: Captured network requests (browser only)
        cookies: List of cookies present after request
    """

    url: str
    status: int
    body: bytes
    headers: dict[str, str] = {}
    engine: EngineType = "curl"
    elapsed: float = 0.0
    proxy_used: str | None = None
    error: str | None = None
    screenshot: bytes | None = None
    action_results: list[ActionResult] = []
    network_log: list[NetworkExchange] = []
    cookies: list[Cookie] = []
    from_cache: bool = False

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status < 400

    @property
    def text(self) -> str:
        """Return the response body as a string."""
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        """
        Return the response body as a JSON object.

        Raises:
            msgspec.DecodeError: If the body is not valid JSON.
        """
        if not self.body:
            return None
        # Strip null bytes which can cause decode errors
        clean_body = self.body.replace(b"\x00", b"")
        return msgspec.json.decode(clean_body)

    def to_page(self) -> "WebPage":
        return WebPage(
            self.body.decode("utf-8", errors="replace"),
            url=self.url,
            metadata={"status": str(self.status), "engine": self.engine},
        )
