import logging
import time
from typing import Any

import httpx

from ...types import Action, BrowserEndpoint, Proxy, Response
from .actions import actions_to_payload

logger = logging.getLogger(__name__)


class BaaSEngine:
    """
    Browser engine using Browser-as-a-Service HTTP API.

    Compatible with:
    - Your custom unblocker
    - Browserless
    - ScrapingBee
    - Any BaaS with similar API
    """

    def __init__(
        self,
        endpoints: list[BrowserEndpoint] | None = None,
        timeout: float = 60.0,
    ):
        """
        Args:
            endpoints: List of BaaS endpoints (load balanced by location)
            timeout: Default request timeout
        """
        self.endpoints = endpoints or []
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """Initialize HTTP client."""
        self._client = httpx.AsyncClient(timeout=self.timeout)

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def add_endpoint(self, endpoint: BrowserEndpoint) -> None:
        """Add a BaaS endpoint."""
        self.endpoints.append(endpoint)

    async def fetch(
        self,
        url: str,
        proxy: Proxy | None = None,
        headers: dict[str, str] | None = None,
        actions: list[Action] | None = None,
        timeout: float | None = None,
        location: str | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Fetch URL via BaaS.

        Args:
            url: Target URL
            proxy: Proxy to use (passed to BaaS)
            headers: Extra headers
            actions: Browser actions
            timeout: Request timeout override
            location: Preferred endpoint location
            **kwargs: Extra params passed to BaaS API

        Returns:
            Response object
        """
        if not self._client:
            return Response(
                url=url,
                status=0,
                body=b"",
                engine="browser",
                error="Client not connected. Call connect() first.",
            )

        endpoint = self._select_endpoint(location)
        if not endpoint:
            return Response(
                url=url,
                status=0,
                body=b"",
                engine="browser",
                error="No BaaS endpoint configured.",
            )

        start = time.perf_counter()
        timeout = timeout or self.timeout

        # Build payload
        payload = {
            "url": url,
            "timeout": int(timeout * 1000),
            **kwargs,
        }

        if proxy:
            payload["proxy"] = proxy.url

        if headers:
            payload["headers"] = headers

        if actions:
            payload["actions"] = actions_to_payload(actions)

        # Auth headers
        request_headers = {}
        if endpoint.api_key:
            request_headers["Authorization"] = f"Bearer {endpoint.api_key}"

        logger.debug(f"[baas] Fetching {url} via {endpoint.url}")

        try:
            resp = await self._client.post(
                endpoint.url,
                json=payload,
                headers=request_headers,
                timeout=timeout,
            )

            data = resp.json()

            # Handle response body (string or bytes)
            body = data.get("body", "")
            if isinstance(body, str):
                body = body.encode("utf-8")

            return Response(
                url=data.get("url", url),
                status=data.get("status", resp.status_code),
                body=body,
                headers=data.get("headers", {}),
                engine="browser",
                elapsed=time.perf_counter() - start,
                proxy_used=proxy.url if proxy else None,
                error=data.get("error"),
            )

        except httpx.TimeoutException:
            return Response(
                url=url,
                status=0,
                body=b"",
                engine="browser",
                elapsed=time.perf_counter() - start,
                proxy_used=proxy.url if proxy else None,
                error="BaaS request timeout",
            )

        except Exception as e:
            logger.error(f"[baas] Error: {e}")
            return Response(
                url=url,
                status=0,
                body=b"",
                engine="browser",
                elapsed=time.perf_counter() - start,
                proxy_used=proxy.url if proxy else None,
                error=str(e),
            )

    def _select_endpoint(self, location: str | None = None) -> BrowserEndpoint | None:
        """Select endpoint, preferring location match."""
        if not self.endpoints:
            return None

        if location:
            for ep in self.endpoints:
                if ep.location == location:
                    return ep

        return self.endpoints[0]
