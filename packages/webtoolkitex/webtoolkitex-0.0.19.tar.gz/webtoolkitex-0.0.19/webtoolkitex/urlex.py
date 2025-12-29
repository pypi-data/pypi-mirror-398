"""
Main Url handling class

@example
url = Url(link = "https://google.com")
response = url.get_response()

url.get_title()
"""

from urllib.parse import unquote, urlparse, parse_qs
from collections import OrderedDict
import urllib.robotparser
import asyncio
import base64

from webtoolkit import (
    WebLogger,
    HttpPageHandler,
    UrlLocation,
    BaseUrl,
    OdyseeVideoHandler,
    OdyseeChannelHandler,
    RedditUrlHandler,
    ReturnDislike,
    GitHubUrlHandler,
    HackerNewsHandler,
    InternetArchive,
    FourChanChannelHandler,
    TwitterUrlHandler,
    YouTubeVideoHandler,
    YouTubeChannelHandler,
)

from .webconfig import WebConfig
from .handlers import (
    YouTubeVideoHandlerJson,
    YouTubeChannelHandlerJson
)

from webtoolkitex.utils.dateutils import DateUtils


class EntryRules(object):
    def get_default_request(url):
        default_request = WebConfig.get_default_request(url)

        location = UrlLocation(url)
        domain_only = location.get_domain_only()
        if domain_only.find("youtube.com") >= 0:
            default_request.crawler_name = "RequestsCrawler"
            default_request.crawler_type = None

        return default_request


class UrlEx(BaseUrl):
    """
    Represents network location
    """

    def __init__(self, url=None, request=None, url_builder=None):
        """
        Constructor. Pass url_builder, if any subsequent calls will be created using this builder.
        """
        if not url_builder:
            url_builder = UrlEx

        super().__init__(url=url, request=request, url_builder=url_builder)

        if self.request.crawler_name and not self.request.crawler_type:
            crawler = WebConfig.get_crawler_from_string(self.request.crawler_name)
            if not crawler:
                WebLogger.error(f"Could not find crawler {crawler}")
                return

            self.request.crawler_type = crawler(url=url)

    def get_request_for_url(self, url):
        """
        Returns request for URL
        """
        return EntryRules.get_default_request(url)

    def get_init_request(self):
        """
        Returns initial request. TODO seems redundant
        """
        request =  EntryRules.get_default_request(url)(self.url)
        request = self.get_request_for_request(request) 
        return request

    def get_request_for_request(self, request):
        """
        Fills necessary fields within request
        """
        if request.crawler_name and request.crawler_type is None:
            crawler = WebConfig.get_crawler_from_string(self.request.crawler_name)
            self.request.crawler_type = crawler(request.url)
        if request.crawler_name is None and request.crawler_type is None:
            default_request = WebConfig.get_default_request(request.url)
            request.crawler_name = default_request.crawler_name
            request.crawler_type = default_request.crawler_type
        return request

    def get_handlers(self):
        """
        Returns available handlers.
        """
        #fmt off
        return [
            YouTubeVideoHandlerJson,
            YouTubeChannelHandlerJson,
            OdyseeVideoHandler,
            OdyseeChannelHandler,
            RedditUrlHandler,
            ReturnDislike,
            GitHubUrlHandler,
            HackerNewsHandler,
            InternetArchive,
            FourChanChannelHandler,
            TwitterUrlHandler,
            YouTubeVideoHandler,        # present here, if somebody wants to call it by name
            YouTubeChannelHandler,      # present here, if somebody wants to call it by name
            HttpPageHandler,            # default
        ]
        #fmt on
