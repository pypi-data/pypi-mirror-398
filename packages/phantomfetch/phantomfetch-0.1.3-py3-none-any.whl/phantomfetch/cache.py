import base64
import hashlib
import json
import time
from pathlib import Path
from typing import Protocol

from loguru import logger

from .telemetry import get_tracer
from .types import CacheStrategy, Response

tracer = get_tracer()


class Cache(Protocol):
    async def get(self, key: str) -> Response | None: ...

    async def set(
        self, key: str, response: Response, ttl: int | None = None
    ) -> None: ...

    def should_cache_request(self, resource_type: str) -> bool: ...


class FileSystemCache:
    def __init__(
        self, cache_dir: str | Path = ".cache", strategy: CacheStrategy = "resources"
    ):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.strategy = strategy

        # Different TTLs for different resource types (in seconds)
        self.ttl_map = {
            "font": 30 * 24 * 60 * 60,  # 30 days
            "image": 14 * 24 * 60 * 60,  # 14 days
            "stylesheet": 14 * 24 * 60 * 60,  # 14 days
            "script": 14 * 24 * 60 * 60,  # 14 days
            "media": 14 * 24 * 60 * 60,  # 14 days
            "manifest": 14 * 24 * 60 * 60,  # 14 days
            "other": 14 * 24 * 60 * 60,  # 14 days
        }

        # Strategy definitions
        self.strategy_map = {
            "all": {
                "document",
                "stylesheet",
                "image",
                "media",
                "font",
                "script",
                "texttrack",
                "xhr",
                "fetch",
                "eventsource",
                "websocket",
                "manifest",
                "other",
            },
            "resources": {
                "stylesheet",
                "image",
                "media",
                "font",
                "script",
                "texttrack",
                "manifest",
            },
            "conservative": {"image", "font", "media"},
        }

        # Tracking/analytics domains to block completely

        # Tracking/analytics domains to block completely
        self.blocked_domains = {
            "fls-na.amazon.com",
            "amazon-adsystem.com",
            "aax-events",
            "adform.net",
            "casalemedia.com",
            "adnxs.com",
            "doubleclick.net",
            "scorecardresearch.com",
            "openx.net",
            "bidswitch.net",
            "facebook.com",
            "rubiconproject.com",
            "pubmatic.com",
            "googlesyndication.com",
            "google-analytics.com",
            "googletagmanager.com",
            "imdb.com/ads",
            "samplicio.us",
            "samba.tv",
            "taboola.com",
            "zeotap.com",
            "yahoo.com/cms",
        }

    def should_block(self, url: str) -> bool:
        """Check if URL should be blocked entirely"""
        return any(domain in url for domain in self.blocked_domains)

    def should_cache_request(self, resource_type: str) -> bool:
        """Check if resource type should be cached based on strategy."""
        allowed_types = self.strategy_map.get(self.strategy, set())
        # If resource_type is None or empty, assume 'other' or 'document' depending on context
        # Playwright might return None for some requests.
        if not resource_type:
            return False

        return resource_type in allowed_types

    def get_cache_key(self, url: str) -> str:
        """Generate a cache key from the URL."""
        return hashlib.md5(url.encode()).hexdigest()

    def get_ttl(self, resource_type: str) -> int:
        """Get TTL in seconds for a resource type."""
        return self.ttl_map.get(resource_type, 14 * 24 * 60 * 60)

    async def get(self, key: str) -> Response | None:
        """
        Retrieve a response from the cache.

        Args:
            key: Cache key (usually the URL)

        Returns:
            Response object if found and not expired, else None
        """
        with tracer.start_as_current_span("phantomfetch.cache.get") as span:
            span.set_attribute("phantomfetch.cache.key", key)

            # Key is expected to be the URL or a composite key
            # For now, we assume key is the URL or we hash it
            # Wrapper for get logic to ensure we set attributes even on early returns if possible,
            # but wait, early returns usually mean no cache or error.

            # The Fetcher passes "engine:url" as key.
            # We should probably strip the engine prefix or handle it.

            # If key contains ':', split it.
            if ":" in key:
                _, url = key.split(":", 1)
            else:
                url = key

            file_key = self.get_cache_key(url)
            file_path = self.cache_dir / f"{file_key}.json"

            if not file_path.exists():
                span.set_attribute("phantomfetch.cache.hit", False)
                return None

            try:
                with open(file_path) as f:
                    data = json.load(f)

                resource_type = data.get("resourceType", "other")
                ttl = self.get_ttl(resource_type)

                if time.time() - data["timestamp"] < ttl:
                    resp_data = data["response"]
                    # Decode body
                    body_bytes = base64.b64decode(resp_data["body"])

                    # Reconstruct Response object
                    span.set_attribute("phantomfetch.cache.hit", True)
                    span.set_attribute("phantomfetch.cache.size_bytes", len(body_bytes))
                    span.set_attribute(
                        "phantomfetch.cache.resource_type", resource_type
                    )

                    return Response(
                        url=resp_data["url"],
                        status=resp_data["status"],
                        body=body_bytes,
                        headers=resp_data.get("headers", {}),
                        engine=resp_data.get("engine", "curl"),
                        elapsed=resp_data.get("elapsed", 0.0),
                        proxy_used=resp_data.get("proxy_used"),
                        error=resp_data.get("error"),
                        # We don't cache screenshot/action_results in this JSON format yet
                        # unless we extend the user's schema.
                        # For now, let's assume basic response caching.
                    )
                else:
                    # Expired
                    span.set_attribute("phantomfetch.cache.hit", False)
                    span.set_attribute("phantomfetch.cache.expired", True)
                    file_path.unlink(missing_ok=True)

            except Exception as e:
                logger.warning(f"[cache] Failed to read cache for {key}: {e}")
                span.record_exception(e)
                return None

            return None

    async def set(self, key: str, response: Response, ttl: int | None = None) -> None:
        """
        Save a response to the cache.

        Args:
            key: Cache key (usually the URL)
            response: Response object to cache
            ttl: Optional TTL override (not used currently, uses ttl_map)
        """
        if ":" in key:
            _, url = key.split(":", 1)
        else:
            url = key

        if self.should_block(url):
            return

        file_key = self.get_cache_key(url)
        file_path = self.cache_dir / f"{file_key}.json"

        # Prepare data
        resp_dict = {
            "url": response.url,
            "status": response.status,
            "body": base64.b64encode(response.body).decode(),
            "headers": response.headers,
            "engine": response.engine,
            "elapsed": response.elapsed,
            "proxy_used": response.proxy_used,
            "error": response.error,
        }

        data = {
            "timestamp": time.time(),
            "response": resp_dict,
            "url": url,
            "resourceType": "other",  # Default for now
        }

        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"[cache] Failed to write cache for {key}: {e}")

    def clear_expired(self) -> None:
        """Remove expired entries from the cache."""
        for file_path in self.cache_dir.glob("*.json"):
            try:
                with open(file_path) as f:
                    data = json.load(f)

                resource_type = data.get("resourceType", "other")
                ttl = self.get_ttl(resource_type)

                if time.time() - data["timestamp"] >= ttl:
                    file_path.unlink()
            except Exception:
                file_path.unlink(missing_ok=True)
