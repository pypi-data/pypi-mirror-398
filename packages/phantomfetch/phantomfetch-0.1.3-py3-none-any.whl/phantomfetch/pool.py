import random
import time
from typing import Any, cast
from urllib.parse import urlparse

from .types import Proxy, ProxyStrategy


class ProxyPool:
    def __init__(
        self, proxies: list[Proxy | str], strategy: ProxyStrategy = "round_robin"
    ):
        self.proxies = [p if isinstance(p, Proxy) else Proxy(url=p) for p in proxies]
        self.strategy = strategy
        self._index = 0
        self._domain_map: dict[str, Proxy] = {}

    def get(self, url: str | None = None, location: str | None = None) -> Proxy | None:
        if not self.proxies:
            return None

        match self.strategy:
            case "round_robin":
                proxy = self.proxies[self._index % len(self.proxies)]
                self._index += 1
                return proxy

            case "random":
                return random.choice(self.proxies)

            case "geo_match" if location:
                candidates = [p for p in self.proxies if p.location == location]
                return random.choice(candidates) if candidates else self.get()

            case "sticky" if url:
                domain = urlparse(url).netloc
                if domain not in self._domain_map:
                    self._domain_map[domain] = random.choice(self.proxies)
                return self._domain_map[domain]

            case "failover":
                return next(
                    (p for p in self.proxies if p.failures < 3), self.proxies[0]
                )

            case _:
                return random.choice(self.proxies)

    def mark_failed(self, proxy: Proxy) -> None:
        proxy.failures += 1

    def mark_success(self, proxy: Proxy) -> None:
        proxy.failures = max(0, proxy.failures - 1)
        proxy.last_used = time.time()

    @classmethod
    def from_locations(
        cls, mapping: dict[str, list[str]], **kwargs: Any
    ) -> "ProxyPool":
        proxies = [
            Proxy(url=url, location=loc)
            for loc, urls in mapping.items()
            for url in urls
        ]
        return cls(cast(list[Proxy | str], proxies), **kwargs)
