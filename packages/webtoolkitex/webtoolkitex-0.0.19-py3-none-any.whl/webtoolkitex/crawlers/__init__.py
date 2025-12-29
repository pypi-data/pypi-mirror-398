"""
Provides various crawling mechanisms, libraries that can crawl.
"""

from .ytdlp import *
from .curlcffi import CurlCffiCrawler
from .httpx import HttpxCrawler
from .stealth import StealthRequestsCrawler
from .httpmorph import HttpMorphCrawler
