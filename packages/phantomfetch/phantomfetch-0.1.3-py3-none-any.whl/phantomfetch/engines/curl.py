import random
import time
from typing import Any, ClassVar, cast

from curl_cffi.requests import AsyncSession, RequestsError
from loguru import logger

from ..telemetry import get_tracer
from ..types import Cookie, Proxy, Response

tracer = get_tracer()


class CurlEngine:
    """
    curl_cffi based HTTP engine with anti-detection and retry logic.
    """

    BROWSER_VERSIONS: ClassVar[list[str]] = [
        "chrome120",
        "chrome119",
        "chrome116",
        "chrome110",
        "chrome107",
        "chrome104",
        "chrome101",
        "chrome99",
        "edge101",
        "edge99",
    ]

    USER_AGENTS: ClassVar[dict[str, list[str]]] = {
        "chrome": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ],
        "edge": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        ],
    }

    RETRY_STATUS_CODES: ClassVar[set[int]] = {429, 500, 502, 503, 504}

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_backoff_base: float = 2.0,
        verify_ssl: bool = True,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        self.verify_ssl = verify_ssl

    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        cookies: dict[str, str] | list[Cookie] | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_on: set[int] | None = None,
        retry_backoff: float | None = None,
        referer: str | None = None,
        allow_redirects: bool = True,
    ) -> Response:
        """
        Fetch URL with automatic retry and anti-detection.

        Args:
            url: Target URL
            proxy: Optional proxy
            headers: Custom headers (merged with generated)
            cookies: Cookies to send with the request
            timeout: Override default timeout
            max_retries: Override default retries
            retry_on: Set of HTTP status codes to retry on (default: {429, 500, 502, 503, 504})
            retry_backoff: Base for exponential backoff (default: 2.0)
            referer: Referer header
            allow_redirects: Follow redirects

        Returns:
            Response object - check .ok or .error
        """
        timeout = timeout or self.timeout
        max_retries = max_retries or self.max_retries
        retry_status_codes = retry_on or self.RETRY_STATUS_CODES
        backoff_base = retry_backoff or self.retry_backoff_base

        start = time.perf_counter()
        last_error: str | None = None
        last_status: int = 0
        last_body: bytes = b""
        last_headers: dict[str, str] = {}

        for attempt in range(max_retries):
            browser_version, user_agent = self._get_browser_config()
            request_headers = self._build_headers(user_agent, referer)

            if headers:
                request_headers.update(headers)

            with tracer.start_as_current_span("phantomfetch.engine.curl") as span:
                span.set_attribute("url.full", url)
                if proxy:
                    span.set_attribute("phantomfetch.proxy", proxy.url)
                    if proxy.url.startswith("socks"):
                        span.set_attribute("phantomfetch.curl.proxy_type", "socks")
                    else:
                        span.set_attribute("phantomfetch.curl.proxy_type", "http")

                browser_version, user_agent = self._get_browser_config()
                span.set_attribute(
                    "phantomfetch.curl.impersonate", str(browser_version)
                )
                span.set_attribute("phantomfetch.curl.user_agent", user_agent)

                request_headers = self._build_headers(user_agent, referer)

                # Initialize curl_kwargs
                curl_kwargs = {
                    "impersonate": cast(Any, browser_version),
                    "timeout": timeout or self.timeout,
                    "allow_redirects": allow_redirects,
                }

                if headers:
                    request_headers.update(headers)
                    # Track custom headers in OTel (useful for debugging)
                    span.set_attribute(
                        "phantomfetch.curl.custom_headers", list(headers.keys())
                    )

                # Add headers to kwargs
                curl_kwargs["headers"] = request_headers

                if cookies:
                    if isinstance(cookies, dict):
                        curl_kwargs["cookies"] = cookies
                    elif isinstance(cookies, list):
                        # Convert list of Cookie objects to dict for simple usage
                        # curl_cffi supports dict or CookieJar. Dict is easiest for now.
                        curl_kwargs["cookies"] = {c.name: c.value for c in cookies}

                if proxy:
                    curl_kwargs["proxies"] = cast(
                        Any, {"http": proxy.url, "https": proxy.url}
                    )

                logger.debug(f"[curl] Attempt {attempt + 1}/{max_retries}: {url}")

                try:
                    async with AsyncSession() as session:
                        resp = await session.get(url, **curl_kwargs)

                        last_status = resp.status_code
                        last_body = resp.content
                        last_headers = dict(cast(Any, resp.headers))

                        # Extract cookies from session (includes cookies from redirects)
                        final_cookies = []
                        for name, value in session.cookies.items():
                            final_cookies.append(Cookie(name=name, value=value))

                        span.set_attribute("http.status_code", resp.status_code)

                        # Success
                        if 200 <= resp.status_code < 400:
                            logger.debug(f"[curl] Success: {url} [{resp.status_code}]")
                            return Response(
                                url=str(resp.url),
                                status=resp.status_code,
                                body=resp.content,
                                headers=dict(cast(Any, resp.headers)),
                                engine="curl",
                                elapsed=time.perf_counter() - start,
                                proxy_used=proxy.url if proxy else None,
                                cookies=final_cookies,
                            )

                        # Retryable
                        if resp.status_code in retry_status_codes:
                            last_error = f"HTTP {resp.status_code}"
                            logger.warning(
                                f"[curl] Retryable {resp.status_code}, attempt {attempt + 1}"
                            )
                            if attempt < max_retries - 1:
                                await self._backoff(attempt, backoff_base)
                                continue

                        # Non-retryable HTTP error - still return response with body
                        return Response(
                            url=str(resp.url),
                            status=resp.status_code,
                            body=resp.content,
                            headers=dict(cast(Any, resp.headers)),
                            engine="curl",
                            elapsed=time.perf_counter() - start,
                            proxy_used=proxy.url if proxy else None,
                            error=f"HTTP {resp.status_code}",
                            cookies=final_cookies,
                        )

                except RequestsError as e:
                    last_error = str(e)
                    logger.warning(f"[curl] RequestsError: {e}, attempt {attempt + 1}")
                    span.record_exception(e)
                    if attempt < max_retries - 1:
                        await self._backoff(attempt, backoff_base)
                        continue
                except Exception as e:
                    logger.error(f"[curl] Error: {e}")
                    span.record_exception(e)
                    return Response(
                        url=url,
                        status=0,
                        body=b"",
                        engine="curl",
                        elapsed=time.perf_counter() - start,
                        proxy_used=proxy.url if proxy else None,
                        error=str(e),
                    )
        # Exhausted retries
        return Response(
            url=url,
            status=last_status,
            body=last_body,
            headers=last_headers,
            engine="curl",
            elapsed=time.perf_counter() - start,
            proxy_used=proxy.url if proxy else None,
            error=last_error or "Max retries exhausted",
        )

    def _get_browser_config(self) -> tuple[str, str]:
        """Random browser version + matching user agent"""
        version = random.choice(self.BROWSER_VERSIONS)
        agents = self.USER_AGENTS.get("edge" if "edge" in version else "chrome")
        if not agents:
            # Fallback
            agents = self.USER_AGENTS["chrome"]
        return version, random.choice(agents)

    def _build_headers(
        self,
        user_agent: str,
        referer: str | None = None,
    ) -> dict[str, str]:
        """Build realistic browser headers"""
        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        if "Chrome" in user_agent:
            chrome_ver = user_agent.split("Chrome/")[1].split(".")[0]
            platform = '"Windows"' if "Windows" in user_agent else '"macOS"'
            headers.update(
                {
                    "sec-ch-ua": f'"Not_A Brand";v="8", "Chromium";v="{chrome_ver}", "Google Chrome";v="{chrome_ver}"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": platform,
                }
            )

        if referer:
            headers["Referer"] = referer

        return headers

    async def _backoff(self, attempt: int, backoff_base: float | None = None) -> None:
        """Exponential backoff with jitter"""
        import asyncio

        base = backoff_base or self.retry_backoff_base
        wait = base**attempt * (0.5 + random.random())
        logger.debug(f"[curl] Backoff: {wait:.2f}s")
        await asyncio.sleep(wait)
