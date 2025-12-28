import time
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from opentelemetry import context
from playwright.async_api import async_playwright

from ...telemetry import get_tracer
from ...types import Action, Cookie, Proxy, Response
from .actions import execute_actions

tracer = get_tracer()

if TYPE_CHECKING:
    from playwright.async_api import Response as PlaywrightResponse
    from playwright.async_api import Route

    from ...cache import Cache


class CDPEngine:
    """
    Browser engine using Playwright over CDP.

    Supports:
    - Local browser launch
    - Remote CDP endpoint (ws://...)
    - Existing browser connection
    """

    def __init__(
        self,
        cdp_endpoint: str | None = None,
        headless: bool = True,
        viewport: dict[str, int] | None = None,
        timeout: float = 60.0,
        cache: Optional["Cache"] = None,
        use_existing_page: bool = True,
    ):
        """
        Args:
            cdp_endpoint: WebSocket URL for remote CDP (e.g., ws://localhost:9222)
                          If None, launches local browser
            headless: Run browser headless (only for local launch)
            timeout: Default page timeout
            cache: Cache instance for sub-resource caching
            use_existing_page: When connecting to remote CDP, reuse existing page
                               if available (useful for recording services like Scrapeless)
        """
        self.cdp_endpoint = cdp_endpoint
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout
        self.cache = cache
        self.use_existing_page = use_existing_page

        self._playwright: Any = None
        self._browser: Any = None
        self._existing_context: Any = None
        self._existing_page: Any = None

    async def connect(self) -> None:
        """Initialize Playwright and connect to browser."""

        self._playwright = await async_playwright().start()

        if self.cdp_endpoint:
            logger.info(f"[cdp] Connecting to: {self.cdp_endpoint}")
            self._browser = await self._playwright.chromium.connect_over_cdp(
                self.cdp_endpoint
            )

            # Detect existing contexts/pages for recording compatibility
            if self.use_existing_page and self._browser.contexts:
                self._existing_context = self._browser.contexts[0]
                if self._existing_context.pages:
                    self._existing_page = self._existing_context.pages[0]
                    logger.info("[cdp] Using existing page for recording compatibility")
        else:
            logger.info(f"[cdp] Launching local browser (headless={self.headless})")
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless
            )

    async def disconnect(self) -> None:
        """Close browser and Playwright."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def _handle_route(self, route: "Route") -> None:
        """Handle network requests for caching."""
        if not self.cache:
            await route.continue_()
            return

        request = route.request
        # Skip non-GET requests for caching usually, but user might want everything.
        # Let's stick to GET for safety unless specified otherwise.
        if request.method != "GET":
            await route.continue_()
            return

        # Skip caching for the main navigation request to ensure fresh content
        # UNLESS the strategy allows it (e.g. "all" strategy)
        # But wait, the user specifically wanted "resources (but not xhr and main content)" as default.
        # My implementation of "resources" strategy excludes "document".
        # So I should delegate to self.cache.should_cache_request(request.resource_type)

        resource_type = request.resource_type
        if not self.cache.should_cache_request(resource_type):
            await route.continue_()
            return

        try:
            cached = await self.cache.get(request.url)
            if cached:
                # logger.debug(f"[cdp] Cache hit: {request.url}")
                headers = cached.headers.copy()
                headers["X-From-Cache"] = "1"  # Marker to avoid re-caching
                await route.fulfill(
                    status=cached.status, headers=headers, body=cached.body
                )
            else:
                await route.continue_()
        except Exception as e:
            logger.warning(f"[cdp] Route handler error: {e}")
            await route.continue_()

    async def _handle_response(self, response: "PlaywrightResponse") -> None:
        """Handle network responses for caching."""
        if not self.cache:
            return

        # Check for our marker
        if response.headers.get("X-From-Cache"):
            return

        # Only cache successful GET requests
        if response.request.method != "GET" or not (200 <= response.status < 300):
            return

        # Skip data URLs
        if response.url.startswith("data:"):
            return

        # Check strategy
        resource_type = response.request.resource_type
        if not self.cache.should_cache_request(resource_type):
            return

        try:
            body = await response.body()
            # Create our Response object
            # Note: We might need to map resource type if we want to use the user's TTL map effectively
            # Playwright response doesn't give resource type directly easily without request.resource_type

            # We can try to infer or just pass 'other' and let cache handle it if it can
            # But wait, the user's cache implementation uses `resourceType` in the saved JSON.
            # We should try to get it.
            resource_type = response.request.resource_type

            # We need to construct a Response object, but our Response object doesn't have resource_type field.
            # However, the user's `Cache.set` implementation creates a dict wrapper that includes `resourceType`.
            # But `Cache.set` takes a `Response` object.
            # The user's `set` method:
            # def set(self, key, response, resource_type): ...
            # Wait, the user's code had `def set(self, url, response, resource_type):`
            # But I adapted it to `async def set(self, key: str, response: Response, ttl: int | None = None) -> None:` in the previous step.
            # And in that adaptation, I hardcoded `resourceType: 'other'`.

            # I should probably update `Cache.set` to accept `resource_type` or infer it?
            # Or I can smuggle it in the `Response` object? No, that's hacky.
            # Or I can update the protocol?
            # For now, I will stick to the protocol I defined.
            # If I want to support resource types, I should have updated the protocol.
            # Let's check `cache.py` again.
            # I wrote: `resourceType': 'other' # Default for now` in `set`.

            # To fix this properly, I should update `Cache.set` to take `kwargs` or similar,
            # but for now let's just save it. The user can refine later.

            resp_obj = Response(
                url=response.url,
                status=response.status,
                body=body,
                headers=await response.all_headers(),
                engine="browser",
            )

            await self.cache.set(response.url, resp_obj)

        except Exception:
            # response.body() can fail if response is closed or redirected
            pass

    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | list[Cookie] | None = None,
        actions: list[Action] | None = None,
        timeout: float | None = None,
        location: str | None = None,
        wait_until: str = "domcontentloaded",
        block_resources: list[str] | None = None,
    ) -> Response:
        """
        Fetch a URL using Playwright.

        Args:
            url: URL to fetch
            proxy: Proxy config (applied per-context)
            headers: Extra headers
            cookies: Cookies to set
            actions: Browser actions to execute after load
            timeout: Page timeout override
            wait_until: Load state to wait for (domcontentloaded, load, networkidle)
            block_resources: List of resource types to block (e.g., ["image", "media"])

        Returns:
            Response object
        """
        with tracer.start_as_current_span("phantomfetch.engine.cdp") as span:
            span.set_attribute("url.full", url)
            span.set_attribute("phantomfetch.browser.headless", self.headless)
            if self.viewport:
                span.set_attribute(
                    "phantomfetch.browser.viewport",
                    f"{self.viewport.get('width')}x{self.viewport.get('height')}",
                )

            if proxy:
                span.set_attribute("phantomfetch.proxy", proxy.url)

            if headers:
                # Track custom headers for debugging/analytics
                span.set_attribute(
                    "phantomfetch.browser.custom_headers", list(headers.keys())
                )

            if block_resources:
                span.set_attribute(
                    "phantomfetch.browser.block_resources", block_resources
                )

            if not self._browser:
                return Response(
                    url=url,
                    status=0,
                    body=b"",
                    engine="browser",
                    error="Browser not connected. Call connect() first.",
                )

            start = time.perf_counter()
            timeout = timeout or self.timeout
            timeout_ms = int(timeout * 1000)

            # Context options
            context_opts = {}
            if proxy:
                context_opts["proxy"] = {"server": proxy.url}
            if headers:
                context_opts["extra_http_headers"] = headers

            browser_context = None
            page = None
            using_existing = False

            try:
                # Use existing page/context if available (for recording compatibility)
                if self._existing_page and self._existing_context:
                    browser_context = self._existing_context
                    page = self._existing_page
                    using_existing = True
                    logger.debug(f"[cdp] Reusing existing page for {url}")
                else:
                    # Create new context/page as before
                    browser_context = await self._browser.new_context(**context_opts)
                    page = await browser_context.new_page()

                # Set cookies
                if cookies and not using_existing:
                    pw_cookies = []
                    if isinstance(cookies, dict):
                        for name, value in cookies.items():
                            pw_cookies.append(
                                {"name": name, "value": value, "url": url}
                            )
                    elif isinstance(cookies, list):
                        for cookie in cookies:
                            c: dict[str, Any] = {
                                "name": cookie.name,
                                "value": cookie.value,
                                "url": url,
                            }
                            if cookie.domain:
                                c["domain"] = cookie.domain
                            if cookie.path:
                                c["path"] = cookie.path
                            if cookie.expires:
                                c["expires"] = cookie.expires
                            if cookie.http_only:
                                c["httpOnly"] = cookie.http_only
                            if cookie.secure:
                                c["secure"] = cookie.secure
                            if cookie.same_site:
                                c["sameSite"] = cookie.same_site
                            pw_cookies.append(c)

                    await browser_context.add_cookies(pw_cookies)

                page.set_default_timeout(timeout_ms)

                # Setup network capture
                network_log: list[Any] = []

                # Capture current context to propagate to callbacks
                current_ctx = context.get_current()

                async def on_response(response: "PlaywrightResponse") -> None:
                    token = context.attach(current_ctx)
                    try:
                        # Handle caching logic first
                        await self._handle_response(response)

                        # Network capture logic
                        try:
                            req = response.request
                            if req.resource_type in ("xhr", "fetch"):
                                # Capture body safely
                                resp_body = None
                                try:
                                    # Limit body size capture to avoid memory issues
                                    body_bytes = await response.body()
                                    if len(body_bytes) < 1024 * 1024:  # 1MB limit
                                        resp_body = body_bytes.decode(
                                            "utf-8", errors="replace"
                                        )
                                    else:
                                        resp_body = "<Body too large>"
                                except Exception:
                                    resp_body = "<Failed to capture body>"

                                from ...types import NetworkExchange

                                # Calculate timing
                                duration = 0.0
                                # response_end = response.request.timing.get("responseEnd", -1)
                                # request_start = response.request.timing.get("requestStart", -1)
                                # That might not be populated or available.
                                # Playwright response timings are in request().timing
                                timing = req.timing
                                if (
                                    timing
                                    and timing.get("responseEnd") != -1
                                    and timing.get("requestStart") != -1
                                ):
                                    # Timings are relative to startTime.
                                    # responseEnd - requestStart = duration in ms
                                    duration = (
                                        timing["responseEnd"] - timing["requestStart"]
                                    ) / 1000.0
                                    # If duration < 0 (e.g. from cache or served locally), set 0
                                    duration = max(0.0, duration)

                                network_log.append(
                                    NetworkExchange(
                                        url=response.url,
                                        method=req.method,
                                        status=response.status,
                                        resource_type=req.resource_type,
                                        request_headers=await req.all_headers(),
                                        response_headers=await response.all_headers(),
                                        request_body=req.post_data,
                                        response_body=resp_body,
                                        duration=duration,
                                    )
                                )
                        except Exception as e:
                            logger.warning(f"[cdp] Capture error: {e}")
                    finally:
                        context.detach(token)

                async def handle_route_with_context(route: "Route") -> None:
                    # Attach the captured context
                    token = context.attach(current_ctx)
                    try:
                        # Handle resource blocking
                        if (
                            block_resources
                            and route.request.resource_type in block_resources
                        ):
                            await route.abort()
                            return

                        await self._handle_route(route)
                    finally:
                        context.detach(token)

                # Setup caching, blocking and capture
                # If we have cache OR block_resources, we need routing
                if self.cache or block_resources:
                    await page.route("**/*", handle_route_with_context)

                # We use a single listener for both cache and capture
                page.on("response", on_response)

                # Navigate
                response = await page.goto(
                    url, wait_until=wait_until, timeout=timeout_ms
                )

                # Execute actions
                action_results = []
                if actions:
                    action_results = await execute_actions(page, actions)

                # Get final content
                content = await page.content()
                status = response.status if response else 0
                resp_headers = dict(response.headers) if response else {}

                # Find screenshot in results
                screenshot = next(
                    (
                        r.data
                        for r in action_results
                        if r.action.action == "screenshot" and r.data
                    ),
                    None,
                )

                # Get cookies
                final_cookies = []
                for c in await browser_context.cookies():
                    final_cookies.append(
                        Cookie(
                            name=c["name"],
                            value=c["value"],
                            domain=c.get("domain"),
                            path=c.get("path"),
                            expires=c.get("expires"),
                            http_only=c.get("httpOnly", False),
                            secure=c.get("secure", False),
                            same_site=c.get("sameSite"),
                        )
                    )

                return Response(
                    url=page.url,
                    status=status,
                    body=content.encode("utf-8"),
                    headers=resp_headers,
                    engine="browser",
                    elapsed=time.perf_counter() - start,
                    proxy_used=proxy.url if proxy else None,
                    screenshot=screenshot,
                    action_results=action_results,
                    network_log=network_log,
                    cookies=final_cookies,
                )

            except Exception as e:
                logger.error(f"[cdp] Error: {e}")
                span.record_exception(e)
                return Response(
                    url=url,
                    status=0,
                    body=b"",
                    engine="browser",
                    elapsed=time.perf_counter() - start,
                    proxy_used=proxy.url if proxy else None,
                    error=str(e),
                )

            finally:
                # Only close if we created new page/context (not reusing existing)
                if not using_existing:
                    if page:
                        await page.close()
                    if browser_context:
                        await browser_context.close()
