import random
import time
import logging
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Centralized manager for proxies with rotation and health checks.
    """

    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies or []
        self.bad_proxies: Dict[str, float] = {}  # proxy -> timestamp of failure
        self.failure_threshold = 3
        self.retry_after = 300  # 5 minutes
        self._current_index = 0

    def add_proxies(self, proxies: List[str]):
        new_proxies = [p for p in proxies if p not in self.proxies]
        self.proxies.extend(new_proxies)

    def get_proxy(self, strategy: str = "random") -> Optional[str]:
        """Returns a healthy proxy based on the rotation strategy."""
        current_time = time.time()

        # Filter out bad proxies that haven't cooled down yet
        healthy_proxies = [
            p
            for p in self.proxies
            if p not in self.bad_proxies
            or (current_time - self.bad_proxies[p] > self.retry_after)
        ]

        if not healthy_proxies:
            logger.warning("No healthy proxies available!")
            return None

        if strategy == "random":
            return random.choice(healthy_proxies)

        elif strategy == "round_robin":
            proxy = healthy_proxies[self._current_index % len(healthy_proxies)]
            self._current_index += 1
            return proxy

        return healthy_proxies[0]

    def mark_failed(self, proxy: str):
        """Marks a proxy as failed and records the time."""
        if proxy in self.proxies:
            logger.warning(f"Marking proxy as FAILED: {proxy}")
            self.bad_proxies[proxy] = time.time()

    def get_all_proxies(self) -> List[str]:
        return self.proxies


# Singleton instance for easy access across the app
proxy_manager = ProxyManager()
