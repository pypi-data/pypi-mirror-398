import logging
import base64
from lazy_crawler.lib.proxy_manager import proxy_manager

logger = logging.getLogger(__name__)


class EnhancedProxyMiddleware:
    """
    Scrapy middleware that uses ProxyManager for rotation and health tracking.
    """

    def __init__(self, rotation_strategy: str = "random"):
        self.strategy = rotation_strategy

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.settings
        # Load proxies from settings into singleton if not already loaded
        proxy_list = settings.getlist("PROXY_LIST")
        if proxy_list:
            proxy_manager.add_proxies(proxy_list)

        strategy = settings.get("PROXY_ROTATION_STRATEGY", "random")
        return cls(rotation_strategy=strategy)

    def process_request(self, request, spider):
        proxy_url = proxy_manager.get_proxy(strategy=self.strategy)
        if proxy_url:
            request.meta["proxy"] = proxy_url
            # Store the current proxy in meta so we can mark it as failed if the request fails
            request.meta["_current_proxy"] = proxy_url
            logger.debug(f"Using rotated proxy: {proxy_url} for {request.url}")
        else:
            logger.warning(
                f"No proxies available for {request.url}, proceeding without proxy."
            )

    def process_exception(self, request, exception, spider):
        """
        Handle request failures. If a proxy was used, mark it as failed.
        """
        current_proxy = request.meta.get("_current_proxy")
        if current_proxy:
            logger.warning(f"Request failed with proxy {current_proxy}: {exception}")
            proxy_manager.mark_failed(current_proxy)
        return None  # Let Scrapy handle the retry
