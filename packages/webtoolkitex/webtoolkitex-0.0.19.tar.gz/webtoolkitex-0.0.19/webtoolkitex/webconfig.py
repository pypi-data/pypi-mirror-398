"""
Provides default web configuratoin
"""

import os
import psutil
from pathlib import Path

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from webtoolkit import (
    RequestsCrawler,
    PageRequestObject,
    WebLogger,
)

from .crawlers import (
    StealthRequestsCrawler,
    CurlCffiCrawler,
    HttpxCrawler,
    YtdlpCrawler,
    HttpMorphCrawler,
)


class WebConfig(object):
    """
    API to configure webtools
    """

    script_operating_dir = None
    script_responses_directory = Path("storage")
    display = None
    browser_mapping = {}
    default_chromedriver_path = Path("/usr/bin/chromedriver")

    def init():
        pass

    def get_crawlers_raw():
        crawlers = [
            RequestsCrawler,
            StealthRequestsCrawler,
            CurlCffiCrawler,
            HttpxCrawler,
            YtdlpCrawler,
            HttpMorphCrawler,
        ]

        return crawlers

    def get_init_crawler_config(headless_script=None, full_script=None, port=None):
        """
        Caller may provide scripts
        """
        mapping = []

        mapping.append(WebConfig.get_default_browser_setup(RequestsCrawler))

        mapping.append(WebConfig.get_default_browser_setup(StealthRequestsCrawler))
        mapping.append(WebConfig.get_default_browser_setup(CurlCffiCrawler))
        mapping.append(WebConfig.get_default_browser_setup(HttpxCrawler))
        mapping.append(WebConfig.get_default_browser_setup(YtdlpCrawler))
        mapping.append(WebConfig.get_default_browser_setup(HttpMorphCrawler))

        return mapping

    def get_crawler_names():
        """
        Returns string representation
        """
        str_crawlers = []
        for crawler in WebConfig.get_crawlers_raw():
            str_crawlers.append(crawler.__name__)

        return str_crawlers

    def get_crawler_from_string(crawler_string):
        """
        Returns crawler for input string
        """
        if not crawler_string:
            return

        crawlers = WebConfig.get_crawlers_raw()
        for crawler in crawlers:
            if crawler.__name__ == crawler_string:
                return crawler

    def get_crawler_from_mapping(request, mapping_data):
        crawler_class = None

        if "crawler" in mapping_data and mapping_data["crawler"]:
            crawler_class = mapping_data["crawler"]

        if "name" in mapping_data and mapping_data["name"]:
            crawler_class = WebConfig.get_crawler_from_string(mapping_data["name"])

        if crawler_class is None and request:
            crawler_class = WebConfig.get_crawler_from_string(request.crawler_type)

        if not crawler_class:
            return

        settings = mapping_data["settings"]

        c = crawler(request=request, settings=settings)
        if c.is_valid():
            return c

    def get_crawlers():
        """
        TODO is this necessary?
        """
        result = []
        mapping = WebConfig.get_init_crawler_config()
        for crawler in mapping:
            result.append(crawler)

        return result

    def get_default_crawler_name():
        return "CurlCffiCrawler"

    def get_default_crawler(url):
        configured_crawlers = WebConfig.get_init_crawler_config()
        for crawler_data in configured_crawlers:
            if crawler_data["name"] == WebConfig.get_default_crawler_name():
                return crawler_data

    def get_default_request(url):
        crawler_data = WebConfig.get_default_crawler(url)
        if crawler_data:
            request = PageRequestObject(url)
            request.crawler_name = crawler_data["name"]
            crawler_class = WebConfig.get_crawler_from_string(request.crawler_name)
            request.crawler_type = crawler_class(url=url)
            return request

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from .utils.logger import PrintLogger

        WebLogger.web_logger = PrintLogger()

    def disable_ssl_warnings():
        disable_warnings(InsecureRequestWarning)

    def get_bytes_limit():
        return 5000000  # 5 MB. There are some RSS more than 1MB

    def get_default_browser_setup(browser, timeout_s=30):
        return {
            "name": browser.__name__,
            "settings": {"timeout_s": timeout_s},
        }

    def get_requests():
        return {
            "name": "RequestsCrawler",
            "settings": {"timeout_s": 40},
        }
