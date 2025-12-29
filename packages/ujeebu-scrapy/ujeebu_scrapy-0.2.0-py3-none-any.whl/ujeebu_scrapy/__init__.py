"""
Ujeebu Scrapy - Scrapy middleware for Ujeebu APIs.

This package provides Scrapy integration for Ujeebu web scraping and
content extraction APIs. It includes request classes for:

- Scrape API: Render JavaScript-heavy pages with a headless browser
- Extract API: Extract article content from news/blog pages
- SERP API: Get search engine results from Google

Example:
    from ujeebu_scrapy import UjeebuScrapeRequest, UjeebuExtractRequest

    # In your spider
    yield UjeebuScrapeRequest(
        url='https://example.com',
        params={'js': True, 'wait_for': 2000},
        callback=self.parse
    )
"""

__author__ = """Ujeebu"""
__email__ = 'y.alhyane@gmail.com'
__version__ = '0.2.0'


from .ujeebu_middleware import UjeebuMiddleware
from .ujeebu_request import (
    UjeebuRequest,
    UjeebuScrapeRequest,
    UjeebuExtractRequest,
    UjeebuSerpRequest,
    UjeebuBaseRequest,
)

__all__ = [
    'UjeebuMiddleware',
    'UjeebuRequest',
    'UjeebuScrapeRequest',
    'UjeebuExtractRequest',
    'UjeebuSerpRequest',
    'UjeebuBaseRequest',
]
