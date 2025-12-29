"""
Similar project: https://pypi.org/project/abstract-webtools/
"""

from .urlex import UrlEx

from .handlers import (
    YouTubeVideoHandlerJson,
    YouTubeChannelHandlerJson,
)

from .crawlers import (
    StealthRequestsCrawler,
    CurlCffiCrawler,
    HttpxCrawler,
    HttpMorphCrawler,
)
