# import os
# import sys
import scrapy
# from scrapy.crawler import CrawlerProcess
# from twisted.internet import reactor
# from scrapy.crawler import CrawlerRunner
# from scrapy.utils.log import configure_logging
# from scrapy.loader import ItemLoader
# from scrapy.utils.project import get_project_settings
# from scrapy.loader import ItemLoader
# from lazy_crawler.lib.user_agent import get_user_agent


class LazyBaseCrawler(scrapy.Spider):
    """
    Base crawler for Lazy Crawler projects.
    Inherit from this class to benefit from pre-configured settings and utilities.
    """

    name = "lazy_base_crawler"
    allowed_domains = []
    start_urls = []

    def playwright_request(self, url, callback, **kwargs):
        """
        Helper to create a Playwright-enabled request.
        """
        meta = kwargs.get("meta", {})
        meta["playwright"] = True
        return scrapy.Request(url, callback=callback, meta=meta, **kwargs)
