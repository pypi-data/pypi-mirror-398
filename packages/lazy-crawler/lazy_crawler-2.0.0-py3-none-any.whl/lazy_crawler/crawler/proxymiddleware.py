import base64
import logging


class ProxyMiddleware:
    def __init__(self, proxy_server, proxy_username, proxy_password):
        self.proxy_server = proxy_server
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        settings = crawler.settings
        proxy_server = settings.get("PROXY_SERVER")
        proxy_username = settings.get("PROXY_USERNAME")
        proxy_password = settings.get("PROXY_PASSWORD")
        return cls(proxy_server, proxy_username, proxy_password)

    def process_request(self, request, spider):
        proxy_url = self.proxy_server
        if self.proxy_username and self.proxy_password:
            credentials = f"{self.proxy_username}:{self.proxy_password}"
            base64_credentials = base64.b64encode(credentials.encode()).decode()
            request.headers["Proxy-Authorization"] = f"Basic {base64_credentials}"

        request.meta["proxy"] = f"http://{proxy_url}"
        logging.info(f"Using proxy: {proxy_url} for URL: {request.url}")
