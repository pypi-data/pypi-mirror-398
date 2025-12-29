"""
Ujeebu Request classes for Scrapy integration.

This module provides request classes for all Ujeebu API endpoints:
- UjeebuScrapeRequest (alias: UjeebuRequest): For the Scrape API
- UjeebuExtractRequest: For the Article Extractor API
- UjeebuSerpRequest: For the SERP (Search Engine Results Page) API
"""

import copy
import json
import logging
import urllib
from urllib.parse import quote_plus

from scrapy import Request
from scrapy.spidermiddlewares.httperror import HttpError

log = logging.getLogger('scrapy.ujeebu')


class UjeebuBaseRequest(Request):
    """Base class for all Ujeebu API requests."""

    # Default API endpoint - to be overridden by subclasses
    ENDPOINT = '/scrape'

    # Request type identifier
    REQUEST_TYPE = 'scrape'

    def __init__(self, url,
                 params=None,
                 headers=None,
                 meta=None,
                 body=None,
                 **kwargs):
        params = params or {}
        meta = copy.deepcopy(meta) or {}

        if headers:
            headers = self.handle_headers(headers)

        # Determine if this is a POST request (for extract_rules or raw_html)
        self.use_post = self._should_use_post(params)

        if self.use_post:
            # For POST requests, we'll handle this in the middleware
            self.post_data = self._prepare_post_data(url, params)
            self.query_params = {}
        else:
            # For GET requests
            query_params = self.handle_ujeebu_params({
                **{'url': url},
                **params
            })
            self.query_params = query_params
            self.post_data = None

        meta['ujeebu'] = {
            'url': url,
            'endpoint': self.ENDPOINT,
            'request_type': self.REQUEST_TYPE,
            'use_post': self.use_post
        }

        errback = kwargs.pop("errback", self.handle_error)

        super().__init__(
            url,
            headers=headers,
            body=body,
            meta=meta,
            errback=errback,
            **kwargs
        )

    def _should_use_post(self, params):
        """Determine if the request should use POST method."""
        return bool('extract_rules' in params and params['extract_rules'])

    def _prepare_post_data(self, url, params):
        """Prepare data for POST request."""
        return {
            'url': url,
            **params
        }

    def get_query_params(self):
        return self.query_params

    @staticmethod
    def handle_url(url):
        return urllib.parse.quote(url)

    @staticmethod
    def handle_custom_js(js):
        return urllib.parse.quote(js)

    @staticmethod
    def handle_headers(headers):
        return {f'Ujb-{k}': v for k, v in headers.items()}

    @staticmethod
    def handle_cookies(cookies):
        if isinstance(cookies, dict):
            stringified_cookies = ';'.join(f'{k}={v}' for k, v in cookies.items())
            return urllib.parse.quote(stringified_cookies)
        elif isinstance(cookies, list):
            # Ujeebu only supports name=value cookies ATM
            raise NotImplementedError
        elif isinstance(cookies, str):
            return cookies

    @classmethod
    def handle_ujeebu_params(cls, params):
        new_params = {}
        for k, v in params.items():
            if v in (None, '', [], {}):
                continue
            elif k == 'url':
                new_params[k] = cls.handle_url(v)
            elif k == 'custom_js':
                new_params[k] = cls.handle_custom_js(v)
            elif k == 'cookies':
                new_params[k] = cls.handle_cookies(v)
            elif k == 'screenshot_partial' and isinstance(v, dict):
                new_params[k] = json.dumps(v)
            else:
                new_params[k] = v
        return new_params

    def handle_error(self, error):
        if error.check(HttpError):
            log.error(
                f'Received an Ujeebu error: {error.value.response.text}')
        else:
            log.error(repr(error))


class UjeebuScrapeRequest(UjeebuBaseRequest):
    """
    Request class for the Ujeebu Scrape API.

    The Scrape API returns web pages after rendering with a headless browser.
    It supports JavaScript execution, screenshots, PDFs, and data extraction.

    Parameters:
        url (str): URL to scrape
        params (dict): Scrape API parameters including:
            - response_type: 'html', 'raw', 'pdf', or 'screenshot'
            - js: Enable JavaScript execution (default: True)
            - custom_js: Custom JavaScript to run on the page
            - wait_for: Wait conditions (ms, selector, or JS callable)
            - extract_rules: Rules for structured data extraction
            - proxy_type: 'rotating', 'advanced', 'premium', 'residential', 'mobile'
            - proxy_country: Country code for geo-targeting
            - device: 'desktop' or 'mobile'
            - scroll_down: Enable page scrolling
            - screenshot_fullpage: Full page screenshot
            - block_ads: Block advertisements
            - And more... See API docs for full list
        headers (dict): Custom headers to forward (auto-prefixed with 'Ujb-')

    Example:
        >>> yield UjeebuScrapeRequest(
        ...     url='https://example.com',
        ...     params={
        ...         'js': True,
        ...         'wait_for': 2000,
        ...         'proxy_type': 'residential'
        ...     },
        ...     callback=self.parse
        ... )
    """

    ENDPOINT = '/scrape'
    REQUEST_TYPE = 'scrape'

    def __init__(self, url,
                 params=None,
                 headers=None,
                 meta=None,
                 body=None,
                 extract_rules=None,
                 response_type='html',
                 js=True,
                 wait_for=None,
                 custom_js=None,
                 proxy_type=None,
                 proxy_country=None,
                 device=None,
                 scroll_down=False,
                 screenshot_fullpage=False,
                 block_ads=False,
                 timeout=None,
                 **kwargs):
        """
        Initialize a Scrape API request.

        Args:
            url: The URL to scrape
            params: Additional API parameters (merged with named params)
            headers: Custom headers to forward
            meta: Scrapy request metadata
            body: Request body
            extract_rules: Rules for structured data extraction
            response_type: Type of response ('html', 'raw', 'pdf', 'screenshot')
            js: Enable JavaScript execution
            wait_for: Wait condition (ms, selector, or JS callable)
            custom_js: Custom JavaScript to execute
            proxy_type: Type of proxy to use
            proxy_country: Country for geo-targeting
            device: Device type ('desktop' or 'mobile')
            scroll_down: Enable scrolling
            screenshot_fullpage: Take full page screenshot
            block_ads: Block advertisements
            timeout: Request timeout in seconds
            **kwargs: Additional Scrapy Request arguments
        """
        params = params or {}

        # Merge named parameters into params dict
        if extract_rules:
            params['extract_rules'] = extract_rules
        if response_type != 'html':
            params['response_type'] = response_type
        if not js:
            params['js'] = js
        if wait_for is not None:
            params['wait_for'] = wait_for
        if custom_js:
            params['custom_js'] = custom_js
        if proxy_type:
            params['proxy_type'] = proxy_type
        if proxy_country:
            params['proxy_country'] = proxy_country
        if device:
            params['device'] = device
        if scroll_down:
            params['scroll_down'] = scroll_down
        if screenshot_fullpage:
            params['screenshot_fullpage'] = screenshot_fullpage
        if block_ads:
            params['block_ads'] = block_ads
        if timeout:
            params['timeout'] = timeout

        super().__init__(
            url,
            params=params,
            headers=headers,
            meta=meta,
            body=body,
            **kwargs
        )


# Alias for backwards compatibility
UjeebuRequest = UjeebuScrapeRequest


class UjeebuExtractRequest(UjeebuBaseRequest):
    """
    Request class for the Ujeebu Extract (Article Extractor) API.

    The Extract API converts news or blog articles into structured JSON data.
    It extracts the main text, HTML, author, publish date, images, and more.

    Parameters:
        url (str): URL of article to extract
        params (dict): Extract API parameters including:
            - js: Enable JavaScript execution
            - text: Extract article text (default: True)
            - html: Extract article HTML (default: True)
            - media: Extract embedded media
            - feeds: Extract RSS feeds
            - images: Extract all images
            - author: Extract author information
            - pub_date: Extract publish date
            - is_article: Return article probability score
            - quick_mode: Use faster analysis mode
            - strip_tags: Tags to strip from extracted HTML
            - And more... See API docs for full list
        headers (dict): Custom headers to forward (auto-prefixed with 'Ujb-')
        raw_html (str): Optional HTML content to extract from instead of fetching

    Example:
        >>> yield UjeebuExtractRequest(
        ...     url='https://example.com/article',
        ...     params={
        ...         'text': True,
        ...         'html': True,
        ...         'images': True
        ...     },
        ...     callback=self.parse_article
        ... )
    """

    ENDPOINT = '/extract'
    REQUEST_TYPE = 'extract'

    def __init__(self, url,
                 params=None,
                 headers=None,
                 meta=None,
                 body=None,
                 raw_html=None,
                 text=True,
                 html=True,
                 images=True,
                 media=False,
                 feeds=False,
                 author=True,
                 pub_date=True,
                 is_article=True,
                 quick_mode=False,
                 js=False,
                 proxy_type=None,
                 timeout=None,
                 **kwargs):
        """
        Initialize an Extract API request.

        Args:
            url: The URL of the article to extract
            params: Additional API parameters (merged with named params)
            headers: Custom headers to forward
            meta: Scrapy request metadata
            body: Request body
            raw_html: HTML content to extract from (instead of fetching URL)
            text: Extract article text
            html: Extract article HTML
            images: Extract images
            media: Extract embedded media
            feeds: Extract RSS feeds
            author: Extract author information
            pub_date: Extract publish date
            is_article: Return article probability score
            quick_mode: Use faster analysis mode
            js: Enable JavaScript execution
            proxy_type: Type of proxy to use
            timeout: Request timeout in seconds
            **kwargs: Additional Scrapy Request arguments
        """
        params = params or {}

        # Store raw_html for POST handling
        self.raw_html = raw_html

        # Build params from named arguments
        if raw_html:
            params['raw_html'] = raw_html
        if not text:
            params['text'] = text
        if not html:
            params['html'] = html
        if not images:
            params['images'] = images
        if media:
            params['media'] = media
        if feeds:
            params['feeds'] = feeds
        if not author:
            params['author'] = author
        if not pub_date:
            params['pub_date'] = pub_date
        if not is_article:
            params['is_article'] = is_article
        if quick_mode:
            params['quick_mode'] = quick_mode
        if js:
            params['js'] = js
        if proxy_type:
            params['proxy_type'] = proxy_type
        if timeout:
            params['timeout'] = timeout

        super().__init__(
            url,
            params=params,
            headers=headers,
            meta=meta,
            body=body,
            **kwargs
        )

    def _should_use_post(self, params):
        """Extract API uses POST when raw_html is provided."""
        return bool('raw_html' in params and params['raw_html'])

    def _prepare_post_data(self, url, params):
        """Prepare form data for POST request with raw_html."""
        return {
            'url': url,
            **params
        }


class UjeebuSerpRequest(UjeebuBaseRequest):
    """
    Request class for the Ujeebu SERP (Search Engine Results Page) API.

    The SERP API retrieves search results from Google with customizable
    parameters for location, language, device type, and search type.

    Parameters:
        search (str): The search query to perform
        params (dict): SERP API parameters including:
            - search_type: 'search', 'images', 'news', 'videos', or 'maps'
            - lang: Language code (e.g., 'en', 'es', 'fr')
            - location: Country code (e.g., 'us', 'uk', 'fr')
            - device: 'desktop', 'mobile', or 'tablet'
            - results_count: Number of results per page
            - page: Results page number
            - extra_params: Additional Google search parameters
        headers (dict): Custom headers to forward (auto-prefixed with 'Ujb-')

    Example:
        >>> yield UjeebuSerpRequest(
        ...     search='python web scraping',
        ...     search_type='search',
        ...     lang='en',
        ...     location='us',
        ...     callback=self.parse_results
        ... )
    """

    ENDPOINT = '/serp'
    REQUEST_TYPE = 'serp'

    def __init__(self,
                 search=None,
                 url=None,
                 params=None,
                 headers=None,
                 meta=None,
                 body=None,
                 search_type='search',
                 lang='en',
                 location='us',
                 device='desktop',
                 results_count=10,
                 page=1,
                 extra_params=None,
                 **kwargs):
        """
        Initialize a SERP API request.

        Note: Either 'search' or 'url' (Google search URL) must be provided.

        Args:
            search: The search query to perform on Google
            url: Alternative: provide a full Google search URL
            params: Additional API parameters (merged with named params)
            headers: Custom headers to forward
            meta: Scrapy request metadata
            body: Request body
            search_type: Type of search ('search', 'images', 'news', 'videos', 'maps')
            lang: Language code for results
            location: Country code for geo-targeting
            device: Device type ('desktop', 'mobile', 'tablet')
            results_count: Number of results per page
            page: Results page number
            extra_params: Additional Google search parameters
            **kwargs: Additional Scrapy Request arguments
        """
        params = params or {}

        if not search and not url:
            raise ValueError("Either 'search' or 'url' must be provided")

        # Build params from named arguments
        if search:
            params['search'] = search
        if search_type != 'search':
            params['search_type'] = search_type
        if lang != 'en':
            params['lang'] = lang
        if location != 'us':
            params['location'] = location
        if device != 'desktop':
            params['device'] = device
        if results_count != 10:
            params['results_count'] = results_count
        if page != 1:
            params['page'] = page
        if extra_params:
            params['extra_params'] = extra_params

        # SERP requests use a placeholder URL since the actual search is API-based
        request_url = url or f"https://www.google.com/search?q={urllib.parse.quote_plus(search or '')}"

        super().__init__(
            request_url,
            params=params,
            headers=headers,
            meta=meta,
            body=body,
            **kwargs
        )

    def _should_use_post(self, params):
        """SERP API always uses GET."""
        return False

    @classmethod
    def handle_ujeebu_params(cls, params):
        """SERP-specific parameter handling."""
        new_params = {}
        for k, v in params.items():
            if v in (None, '', [], {}):
                continue
            elif k == 'url':
                new_params[k] = cls.handle_url(v)
            elif k == 'search':
                # Don't encode search query - let the API handle it
                new_params[k] = v
            else:
                new_params[k] = v
        return new_params

