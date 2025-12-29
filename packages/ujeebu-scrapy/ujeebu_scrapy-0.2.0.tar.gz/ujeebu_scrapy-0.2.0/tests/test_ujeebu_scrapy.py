#!/usr/bin/env python

"""Tests for `ujeebu_scrapy` package."""

import pytest
import json
from unittest.mock import MagicMock, patch

from ujeebu_scrapy import (
    UjeebuMiddleware,
    UjeebuRequest,
    UjeebuScrapeRequest,
    UjeebuExtractRequest,
    UjeebuSerpRequest,
    UjeebuBaseRequest,
)


class TestUjeebuScrapeRequest:
    """Tests for UjeebuScrapeRequest class."""

    def test_basic_request(self):
        """Test basic scrape request creation."""
        request = UjeebuScrapeRequest(
            url='https://example.com',
            callback=lambda x: x
        )
        assert request.url == 'https://example.com'
        assert 'ujeebu' in request.meta
        assert request.meta['ujeebu']['url'] == 'https://example.com'
        assert request.meta['ujeebu']['endpoint'] == '/scrape'
        assert request.meta['ujeebu']['request_type'] == 'scrape'

    def test_request_with_params(self):
        """Test scrape request with params."""
        request = UjeebuScrapeRequest(
            url='https://example.com',
            params={
                'js': True,
                'wait_for': 2000,
                'proxy_type': 'premium'
            },
            callback=lambda x: x
        )
        assert 'url' in request.query_params
        assert request.query_params.get('js') == True
        assert request.query_params.get('wait_for') == 2000
        assert request.query_params.get('proxy_type') == 'premium'

    def test_request_with_named_params(self):
        """Test scrape request with named parameters."""
        request = UjeebuScrapeRequest(
            url='https://example.com',
            js=True,
            wait_for=3000,
            proxy_type='residential',
            scroll_down=True,
            callback=lambda x: x
        )
        # Named params should be in query_params
        assert request.query_params.get('wait_for') == 3000
        assert request.query_params.get('proxy_type') == 'residential'
        assert request.query_params.get('scroll_down') == True

    def test_request_with_extract_rules(self):
        """Test that extract_rules triggers POST mode."""
        extract_rules = {
            'title': {'selector': 'h1', 'type': 'text'}
        }
        request = UjeebuScrapeRequest(
            url='https://example.com',
            extract_rules=extract_rules,
            callback=lambda x: x
        )
        assert request.meta['ujeebu']['use_post'] == True
        assert request.post_data is not None
        assert 'extract_rules' in request.post_data

    def test_request_with_headers(self):
        """Test that custom headers are prefixed with Ujb-."""
        request = UjeebuScrapeRequest(
            url='https://example.com',
            headers={'Authorization': 'Bearer token'},
            callback=lambda x: x
        )
        # Headers should be prefixed
        assert b'Ujb-Authorization' in request.headers or 'Ujb-Authorization' in dict(request.headers)

    def test_request_with_cookies(self):
        """Test cookie handling."""
        request = UjeebuScrapeRequest(
            url='https://example.com',
            params={'cookies': {'session': 'abc123', 'user': 'test'}},
            callback=lambda x: x
        )
        # Cookies should be serialized
        assert 'cookies' in request.query_params

    def test_ujeebu_request_alias(self):
        """Test that UjeebuRequest is an alias for UjeebuScrapeRequest."""
        assert UjeebuRequest is UjeebuScrapeRequest


class TestUjeebuExtractRequest:
    """Tests for UjeebuExtractRequest class."""

    def test_basic_extract_request(self):
        """Test basic extract request creation."""
        request = UjeebuExtractRequest(
            url='https://example.com/article',
            callback=lambda x: x
        )
        assert request.url == 'https://example.com/article'
        assert request.meta['ujeebu']['endpoint'] == '/extract'
        assert request.meta['ujeebu']['request_type'] == 'extract'

    def test_extract_with_options(self):
        """Test extract request with various options."""
        request = UjeebuExtractRequest(
            url='https://example.com/article',
            text=True,
            html=True,
            images=True,
            author=True,
            pub_date=True,
            media=True,
            feeds=True,
            callback=lambda x: x
        )
        # These should be in query_params
        assert request.query_params.get('media') == True
        assert request.query_params.get('feeds') == True

    def test_extract_with_raw_html(self):
        """Test that raw_html triggers POST mode."""
        request = UjeebuExtractRequest(
            url='https://example.com/article',
            raw_html='<html><body>Test content</body></html>',
            callback=lambda x: x
        )
        assert request.meta['ujeebu']['use_post'] == True
        assert request.post_data is not None
        assert 'raw_html' in request.post_data

    def test_extract_quick_mode(self):
        """Test quick mode parameter."""
        request = UjeebuExtractRequest(
            url='https://example.com/article',
            quick_mode=True,
            callback=lambda x: x
        )
        assert request.query_params.get('quick_mode') == True


class TestUjeebuSerpRequest:
    """Tests for UjeebuSerpRequest class."""

    def test_basic_serp_request(self):
        """Test basic SERP request creation."""
        request = UjeebuSerpRequest(
            search='python web scraping',
            callback=lambda x: x
        )
        assert 'google.com' in request.url
        assert request.meta['ujeebu']['endpoint'] == '/serp'
        assert request.meta['ujeebu']['request_type'] == 'serp'

    def test_serp_with_options(self):
        """Test SERP request with various options."""
        request = UjeebuSerpRequest(
            search='test query',
            search_type='news',
            lang='fr',
            location='fr',
            device='mobile',
            results_count=20,
            page=2,
            callback=lambda x: x
        )
        assert request.query_params.get('search') == 'test query'
        assert request.query_params.get('search_type') == 'news'
        assert request.query_params.get('lang') == 'fr'
        assert request.query_params.get('location') == 'fr'
        assert request.query_params.get('device') == 'mobile'
        assert request.query_params.get('results_count') == 20
        assert request.query_params.get('page') == 2

    def test_serp_requires_search_or_url(self):
        """Test that SERP request requires search or url."""
        with pytest.raises(ValueError):
            UjeebuSerpRequest(callback=lambda x: x)

    def test_serp_with_url(self):
        """Test SERP request with Google URL."""
        request = UjeebuSerpRequest(
            url='https://www.google.com/search?q=test',
            callback=lambda x: x
        )
        assert request.url == 'https://www.google.com/search?q=test'

    def test_serp_never_uses_post(self):
        """Test that SERP never uses POST."""
        request = UjeebuSerpRequest(
            search='test',
            callback=lambda x: x
        )
        assert request.meta['ujeebu']['use_post'] == False


class TestUjeebuMiddleware:
    """Tests for UjeebuMiddleware class."""

    def test_middleware_disabled(self):
        """Test middleware when disabled."""
        settings = MagicMock()
        settings.get = lambda key, default=None: {
            'UJEEBU_ENABLED': False,
            'UJEEBU_API_KEY': 'test-key'
        }.get(key, default)

        middleware = UjeebuMiddleware(settings)
        assert middleware.enabled == False

    def test_middleware_requires_api_key(self):
        """Test that middleware requires API key when enabled."""
        from scrapy.exceptions import NotConfigured

        settings = MagicMock()
        settings.get = lambda key, default=None: {
            'UJEEBU_ENABLED': True,
            'UJEEBU_API_KEY': None
        }.get(key, default)

        with pytest.raises(NotConfigured):
            UjeebuMiddleware(settings)

    def test_middleware_processes_ujeebu_requests(self):
        """Test that middleware processes Ujeebu requests."""
        settings = MagicMock()
        settings.get = lambda key, default=None: {
            'UJEEBU_ENABLED': True,
            'UJEEBU_API_KEY': 'test-api-key',
            'UJEEBU_BASE_URL': 'https://api.ujeebu.com',
            'UJEEBU_DEFAULT_PROXY_TYPE': None,
            'UJEEBU_DEFAULT_TIMEOUT': 60
        }.get(key, default)

        middleware = UjeebuMiddleware(settings)

        # Create a scrape request
        request = UjeebuScrapeRequest(
            url='https://example.com',
            params={'js': True},
            callback=lambda x: x
        )

        # Process the request
        spider = MagicMock()
        new_request = middleware.process_request(request, spider)

        # Should return a new request with Ujeebu URL
        assert new_request is not None
        assert 'api.ujeebu.com' in new_request.url
        assert '/scrape' in new_request.url

        # API key should be in headers, not URL
        # Scrapy converts header names to bytes with first letter capitalized
        assert b'Apikey' in new_request.headers or 'Apikey' in new_request.headers
        # Check the value (Scrapy stores header values as lists of bytes)
        apikey_value = new_request.headers.get(b'Apikey') or new_request.headers.get('Apikey')
        assert apikey_value == [b'test-api-key'] or apikey_value == b'test-api-key' or apikey_value == 'test-api-key'

    def test_middleware_ignores_regular_requests(self):
        """Test that middleware ignores non-Ujeebu requests."""
        from scrapy import Request

        settings = MagicMock()
        settings.get = lambda key, default=None: {
            'UJEEBU_ENABLED': True,
            'UJEEBU_API_KEY': 'test-api-key',
        }.get(key, default)

        middleware = UjeebuMiddleware(settings)

        # Create a regular Scrapy request
        request = Request(url='https://example.com', callback=lambda x: x)

        # Process the request
        spider = MagicMock()
        result = middleware.process_request(request, spider)

        # Should return None (don't modify)
        assert result is None


class TestParameterHandling:
    """Tests for parameter handling utilities."""

    def test_url_encoding(self):
        """Test URL encoding."""
        encoded = UjeebuBaseRequest.handle_url('https://example.com/path?q=test')
        assert '%' in encoded  # Should be URL encoded

    def test_custom_js_encoding(self):
        """Test custom JS encoding."""
        js_code = "document.querySelector('.btn').click()"
        encoded = UjeebuBaseRequest.handle_custom_js(js_code)
        assert '%' in encoded  # Should be URL encoded

    def test_cookie_dict_handling(self):
        """Test cookie dict serialization."""
        cookies = {'session': 'abc123', 'user': 'test'}
        result = UjeebuBaseRequest.handle_cookies(cookies)
        assert 'session' in result or 'session%' in result

    def test_cookie_string_passthrough(self):
        """Test cookie string passthrough."""
        cookies = 'session=abc123; user=test'
        result = UjeebuBaseRequest.handle_cookies(cookies)
        assert result == cookies

    def test_header_prefixing(self):
        """Test header prefixing with Ujb-."""
        headers = {'Authorization': 'Bearer token', 'Custom': 'value'}
        result = UjeebuBaseRequest.handle_headers(headers)
        assert 'Ujb-Authorization' in result
        assert 'Ujb-Custom' in result
        assert result['Ujb-Authorization'] == 'Bearer token'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
