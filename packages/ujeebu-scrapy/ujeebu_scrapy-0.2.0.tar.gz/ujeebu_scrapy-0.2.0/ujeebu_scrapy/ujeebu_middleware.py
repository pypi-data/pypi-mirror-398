"""
Ujeebu Scrapy Middleware.

This middleware processes requests using Ujeebu APIs (Scrape, Extract, SERP).
It automatically routes UjeebuRequest classes through the appropriate Ujeebu API endpoint.
"""

import json
import logging

from scrapy import Request
from scrapy.exceptions import NotConfigured
from scrapy.http import TextResponse

from .ujeebu_request import (
    UjeebuBaseRequest,
    UjeebuScrapeRequest,
    UjeebuExtractRequest,
    UjeebuSerpRequest,
    UjeebuRequest,
)

log = logging.getLogger('scrapy.ujeebu')


class UjeebuMiddleware:
    """
    Scrapy middleware that routes requests through Ujeebu APIs.

    This middleware intercepts UjeebuRequest, UjeebuScrapeRequest,
    UjeebuExtractRequest, and UjeebuSerpRequest instances and routes them
    through the appropriate Ujeebu API endpoint.

    Settings:
        UJEEBU_ENABLED (bool): Enable/disable the middleware (default: True)
        UJEEBU_API_KEY (str): Your Ujeebu API key (required)
        UJEEBU_BASE_URL (str): API base URL (default: https://api.ujeebu.com)
        UJEEBU_DEFAULT_PROXY_TYPE (str): Default proxy type (default: None)
        UJEEBU_DEFAULT_TIMEOUT (int): Default timeout in seconds (default: 60)
    """

    def __init__(self, settings):
        self.enabled = settings.get('UJEEBU_ENABLED', True)
        self.api_key = settings.get('UJEEBU_API_KEY')

        if self.enabled and not self.api_key:
            log.error('[UjeebuAPI] API key not found. Set UJEEBU_API_KEY in settings.')
            raise NotConfigured('UJEEBU_API_KEY is required when UJEEBU_ENABLED is True')

        self.base_url = settings.get('UJEEBU_BASE_URL', 'https://api.ujeebu.com')
        self.default_proxy_type = settings.get('UJEEBU_DEFAULT_PROXY_TYPE')
        self.default_timeout = settings.get('UJEEBU_DEFAULT_TIMEOUT', 60)

        if self.enabled:
            log.info(f'[UjeebuAPI] Ujeebu API middleware enabled (base_url: {self.base_url})')

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        """Process a request using the Ujeebu API if applicable."""

        if not self.enabled:
            log.debug('[UjeebuAPI] Middleware disabled, skipping request')
            return None

        # Check if this is a Ujeebu request
        if not isinstance(request, UjeebuBaseRequest):
            return None

        # Get request metadata
        ujeebu_meta = request.meta.get('ujeebu', {})
        endpoint = ujeebu_meta.get('endpoint', '/scrape')
        use_post = ujeebu_meta.get('use_post', False)

        if use_post:
            return self._build_post_request(request, endpoint)
        else:
            return self._build_get_request(request, endpoint)

    def _build_get_request(self, request, endpoint):
        """Build a GET request to Ujeebu API."""
        ujeebu_params = request.query_params.copy()

        # Apply default settings
        if self.default_proxy_type and 'proxy_type' not in ujeebu_params:
            ujeebu_params['proxy_type'] = self.default_proxy_type
        if self.default_timeout and 'timeout' not in ujeebu_params:
            ujeebu_params['timeout'] = self.default_timeout

        ujeebu_url = self._build_ujeebu_url(endpoint, ujeebu_params)

        # Prepare headers with API key
        headers = dict(request.headers) if request.headers else {}
        headers['apiKey'] = self.api_key

        log.debug(f'[UjeebuAPI] GET request to {endpoint}: {ujeebu_url[:100]}...')

        return request.replace(
            cls=Request,
            url=ujeebu_url,
            method='GET',
            headers=headers,
            meta=request.meta
        )

    def _build_post_request(self, request, endpoint):
        """Build a POST request to Ujeebu API."""
        post_data = request.post_data.copy()

        # Apply default settings
        if self.default_proxy_type and 'proxy_type' not in post_data:
            post_data['proxy_type'] = self.default_proxy_type
        if self.default_timeout and 'timeout' not in post_data:
            post_data['timeout'] = self.default_timeout

        ujeebu_url = f'{self.base_url}{endpoint}'

        # Prepare headers with API key
        headers = dict(request.headers) if request.headers else {}
        headers['apiKey'] = self.api_key

        # Handle different content types
        if endpoint == '/extract' and 'raw_html' in post_data:
            # Extract API with raw_html uses form data
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            body = '&'.join(f'{k}={v}' for k, v in post_data.items())
        else:
            # Scrape API with extract_rules uses JSON
            headers['Content-Type'] = 'application/json'
            body = json.dumps(post_data)

        log.debug(f'[UjeebuAPI] POST request to {endpoint}')

        return request.replace(
            cls=Request,
            url=ujeebu_url,
            method='POST',
            headers=headers,
            body=body,
            meta=request.meta
        )

    def process_response(self, request, response, spider):
        """Process a response coming from Ujeebu API if applicable."""

        if 'ujeebu' not in request.meta:
            return response

        ujeebu_meta = request.meta['ujeebu']
        original_url = ujeebu_meta.get('url', request.url)

        # Log response details
        log.debug(f'[UjeebuAPI] Response received for {original_url} (status: {response.status})')

        # Check for Ujeebu-specific headers
        credits_used = response.headers.get(b'Ujb-Credits', b'').decode('utf-8', errors='ignore')
        if credits_used:
            log.debug(f'[UjeebuAPI] Credits used: {credits_used}')

        # Replace URL with the original URL
        return response.replace(url=original_url)

    def process_exception(self, request, exception, spider):
        """Handle exceptions from Ujeebu API requests."""
        if 'ujeebu' in request.meta:
            log.error(f'[UjeebuAPI] Request failed: {exception}')
        return None

    def _build_ujeebu_url(self, endpoint, query_params):
        """Build the full Ujeebu API URL with query parameters."""
        qs = '&'.join(f'{k}={v}' for k, v in query_params.items() if v is not None)
        return f'{self.base_url}{endpoint}?{qs}'
