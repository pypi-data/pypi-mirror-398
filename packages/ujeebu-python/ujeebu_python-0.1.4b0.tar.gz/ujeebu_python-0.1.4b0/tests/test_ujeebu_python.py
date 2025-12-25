#!/usr/bin/env python

"""Tests for `ujeebu_python` package."""

import json
import unittest
from unittest.mock import patch, MagicMock

from ujeebu_python import UjeebuClient


class TestUjeebuClientInit(unittest.TestCase):
    """Tests for UjeebuClient initialization."""

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        client = UjeebuClient(api_key='test_api_key')
        self.assertEqual(client.api_key, 'test_api_key')
        self.assertEqual(client.base_url, 'https://api.ujeebu.com')
        self.assertEqual(client.timeout, 120)

    def test_init_with_custom_base_url(self):
        """Test initialization with custom base URL."""
        client = UjeebuClient(api_key='test_api_key', base_url='https://custom.api.com')
        self.assertEqual(client.base_url, 'https://custom.api.com')

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout."""
        client = UjeebuClient(api_key='test_api_key', timeout=60)
        self.assertEqual(client.timeout, 60)

    def test_init_without_api_key_raises_error(self):
        """Test initialization without API key raises ValueError."""
        with self.assertRaises(ValueError) as context:
            UjeebuClient()
        self.assertEqual(str(context.exception), 'api_key is required')

    def test_init_with_none_api_key_raises_error(self):
        """Test initialization with None API key raises ValueError."""
        with self.assertRaises(ValueError):
            UjeebuClient(api_key=None)


class TestUjeebuClientStaticMethods(unittest.TestCase):
    """Tests for UjeebuClient static methods."""

    def test_handle_url(self):
        """Test handle_url returns URL unchanged."""
        url = 'https://example.com/path?query=value'
        self.assertEqual(UjeebuClient.handle_url(url), url)

    def test_handle_custom_js(self):
        """Test handle_custom_js encodes JavaScript."""
        js = 'console.log("hello world");'
        result = UjeebuClient.handle_custom_js(js)
        self.assertEqual(result, 'console.log%28%22hello+world%22%29%3B')

    def test_handle_headers_none(self):
        """Test handle_headers with None returns None."""
        self.assertIsNone(UjeebuClient.handle_headers(None))

    def test_handle_headers_with_dict(self):
        """Test handle_headers prefixes keys with Ujb-."""
        headers = {'Content-Type': 'application/json', 'Accept': 'text/html'}
        result = UjeebuClient.handle_headers(headers)
        self.assertEqual(result, {
            'Ujb-Content-Type': 'application/json',
            'Ujb-Accept': 'text/html'
        })

    def test_handle_cookies_none(self):
        """Test handle_cookies with None returns None."""
        self.assertIsNone(UjeebuClient.handle_cookies(None))

    def test_handle_cookies_with_dict(self):
        """Test handle_cookies with dict returns URL-encoded string."""
        cookies = {'session': 'abc123', 'user': 'test'}
        result = UjeebuClient.handle_cookies(cookies)
        # The result is URL-encoded, so = becomes %3D and ; becomes %3B
        self.assertIn('session%3Dabc123', result)
        self.assertIn('user%3Dtest', result)

    def test_handle_cookies_with_string(self):
        """Test handle_cookies with string returns string as-is."""
        cookies = 'session=abc123; user=test'
        result = UjeebuClient.handle_cookies(cookies)
        self.assertEqual(result, cookies)

    def test_handle_cookies_with_list_raises_not_implemented(self):
        """Test handle_cookies with list raises NotImplementedError."""
        cookies = [{'name': 'session', 'value': 'abc123'}]
        with self.assertRaises(NotImplementedError):
            UjeebuClient.handle_cookies(cookies)

    def test_handle_ujeebu_params_url(self):
        """Test handle_ujeebu_params handles url parameter."""
        params = {'url': 'https://example.com'}
        result = UjeebuClient.handle_ujeebu_params(params)
        self.assertEqual(result['url'], 'https://example.com')

    def test_handle_ujeebu_params_custom_js(self):
        """Test handle_ujeebu_params handles custom_js parameter."""
        params = {'custom_js': 'alert("test")'}
        result = UjeebuClient.handle_ujeebu_params(params)
        self.assertEqual(result['custom_js'], 'alert%28%22test%22%29')

    def test_handle_ujeebu_params_screenshot_partial(self):
        """Test handle_ujeebu_params handles screenshot_partial dict."""
        params = {'screenshot_partial': {'selector': '#main'}}
        result = UjeebuClient.handle_ujeebu_params(params)
        self.assertEqual(result['screenshot_partial'], '{"selector": "#main"}')

    def test_handle_ujeebu_params_cookies(self):
        """Test handle_ujeebu_params handles cookies parameter."""
        params = {'cookies': {'session': 'abc123'}}
        result = UjeebuClient.handle_ujeebu_params(params)
        self.assertEqual(result['cookies'], 'session%3Dabc123')

    def test_handle_ujeebu_params_empty_values(self):
        """Test handle_ujeebu_params handles empty values."""
        params = {'empty_str': '', 'empty_list': [], 'empty_dict': {}, 'none_val': None}
        result = UjeebuClient.handle_ujeebu_params(params)
        self.assertEqual(result, params)


class TestUjeebuClientExtract(unittest.TestCase):
    """Tests for UjeebuClient.extract method."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_extract_basic(self, mock_get):
        """Test basic extract call."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        result = self.client.extract('https://example.com')

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('url', call_args.kwargs['params'])
        self.assertEqual(call_args.kwargs['params']['url'], 'https://example.com')
        self.assertEqual(call_args.kwargs['params']['apiKey'], 'test_api_key')


    @patch('ujeebu_python.ujeebu_python.requests.post')
    def test_extract_with_raw_html(self, mock_post):
        """Test extract with raw_html uses POST."""
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        self.client.extract('https://example.com', params={'raw_html': '<html></html>'})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args.kwargs['data']['raw_html'], '<html></html>')
        self.assertIn('apiKey', call_args.kwargs['headers'])

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_extract_with_headers(self, mock_get):
        """Test extract with custom headers."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.extract('https://example.com', headers={'Accept': 'text/html'})

        call_args = mock_get.call_args
        self.assertIn('Ujb-Accept', call_args.kwargs['headers'])


class TestUjeebuClientScrape(unittest.TestCase):
    """Tests for UjeebuClient.scrape method."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_scrape_basic(self, mock_get):
        """Test basic scrape call."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        result = self.client.scrape('https://example.com')

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIn('url', call_args.kwargs['params'])


    @patch('ujeebu_python.ujeebu_python.requests.post')
    def test_scrape_with_extract_rules(self, mock_post):
        """Test scrape with extract_rules uses POST."""
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        rules = {'title': 'h1'}
        self.client.scrape('https://example.com', params={'extract_rules': rules})

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        data = json.loads(call_args.kwargs['data'])
        self.assertEqual(data['extract_rules'], rules)

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_scrape_with_headers(self, mock_get):
        """Test scrape with custom headers."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.scrape('https://example.com', headers={'Accept': 'text/html'})

        call_args = mock_get.call_args
        self.assertIn('Ujb-Accept', call_args.kwargs['headers'])


class TestUjeebuClientSerp(unittest.TestCase):
    """Tests for UjeebuClient.serp method."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_serp_basic(self, mock_get):
        """Test basic serp call."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.serp(params={'search': 'test query'})

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['params']['search'], 'test query')
        self.assertEqual(call_args.kwargs['params']['apiKey'], 'test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_serp_with_headers(self, mock_get):
        """Test serp with custom headers."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.serp(params={'search': 'test'}, headers={'Accept': 'application/json'})

        call_args = mock_get.call_args
        self.assertIn('Ujb-Accept', call_args.kwargs['headers'])


class TestUjeebuClientPreview(unittest.TestCase):
    """Tests for UjeebuClient.preview method."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_preview_basic(self, mock_get):
        """Test basic preview call."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.preview('https://example.com')

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['params']['url'], 'https://example.com')
        self.assertEqual(call_args.kwargs['params']['apikey'], 'test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_preview_uses_timeout(self, mock_get):
        """Test preview uses client timeout."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        client = UjeebuClient(api_key='test_api_key', timeout=60)
        client.preview('https://example.com')

        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['timeout'], 60)


class TestUjeebuClientHelperMethods(unittest.TestCase):
    """Tests for UjeebuClient helper methods."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch.object(UjeebuClient, 'scrape')
    def test_get_pdf(self, mock_scrape):
        """Test get_pdf calls scrape with correct params."""
        mock_response = MagicMock()
        mock_scrape.return_value = mock_response

        self.client.get_pdf('https://example.com')

        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        self.assertEqual(call_args[0][0], 'https://example.com')
        self.assertEqual(call_args[0][1]['response_type'], 'pdf')
        self.assertTrue(call_args[0][1]['json'])


    @patch.object(UjeebuClient, 'scrape')
    def test_get_screenshot(self, mock_scrape):
        """Test get_screenshot calls scrape with correct params."""
        mock_response = MagicMock()
        mock_scrape.return_value = mock_response

        self.client.get_screenshot('https://example.com')

        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        self.assertEqual(call_args[0][0], 'https://example.com')
        self.assertEqual(call_args[0][1]['response_type'], 'screenshot')
        self.assertTrue(call_args[0][1]['json'])


    @patch.object(UjeebuClient, 'scrape')
    def test_scrape_with_rules(self, mock_scrape):
        """Test scrape_with_rules calls scrape with correct params."""
        mock_response = MagicMock()
        mock_scrape.return_value = mock_response

        rules = {'title': 'h1', 'links': 'a'}
        self.client.scrape_with_rules('https://example.com', rules)

        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        self.assertEqual(call_args[0][0], 'https://example.com')
        self.assertEqual(call_args[0][1]['extract_rules'], rules)
        self.assertTrue(call_args[0][1]['json'])


    @patch.object(UjeebuClient, 'scrape')
    def test_get_html(self, mock_scrape):
        """Test get_html calls scrape with correct params."""
        mock_response = MagicMock()
        mock_scrape.return_value = mock_response

        self.client.get_html('https://example.com')

        mock_scrape.assert_called_once()
        call_args = mock_scrape.call_args
        self.assertEqual(call_args[0][0], 'https://example.com')
        self.assertEqual(call_args[0][1]['response_type'], 'html')
        self.assertTrue(call_args[0][1]['json'])



class TestUjeebuClientSerpHelpers(unittest.TestCase):
    """Tests for UjeebuClient SERP helper methods."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch.object(UjeebuClient, 'serp')
    def test_search_text(self, mock_serp):
        """Test search_text calls serp with correct params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_text('test query')

        mock_serp.assert_called_once()
        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['search'], 'test query')
        self.assertEqual(call_args[0][0]['search_type'], 'search')

    @patch.object(UjeebuClient, 'serp')
    def test_search_text_with_params(self, mock_serp):
        """Test search_text with additional params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_text('test query', params={'num': 10})

        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['num'], 10)

    @patch.object(UjeebuClient, 'serp')
    def test_search_news(self, mock_serp):
        """Test search_news calls serp with correct params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_news('test query')

        mock_serp.assert_called_once()
        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['search'], 'test query')
        self.assertEqual(call_args[0][0]['search_type'], 'news')

    @patch.object(UjeebuClient, 'serp')
    def test_search_images(self, mock_serp):
        """Test search_images calls serp with correct params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_images('test query')

        mock_serp.assert_called_once()
        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['search'], 'test query')
        self.assertEqual(call_args[0][0]['search_type'], 'images')

    @patch.object(UjeebuClient, 'serp')
    def test_search_videos(self, mock_serp):
        """Test search_videos calls serp with correct params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_videos('test query')

        mock_serp.assert_called_once()
        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['search'], 'test query')
        self.assertEqual(call_args[0][0]['search_type'], 'videos')

    @patch.object(UjeebuClient, 'serp')
    def test_search_maps(self, mock_serp):
        """Test search_maps calls serp with correct params."""
        mock_response = MagicMock()
        mock_serp.return_value = mock_response

        self.client.search_maps('test query')

        mock_serp.assert_called_once()
        call_args = mock_serp.call_args
        self.assertEqual(call_args[0][0]['search'], 'test query')
        self.assertEqual(call_args[0][0]['search_type'], 'maps')


class TestUjeebuClientAccount(unittest.TestCase):
    """Tests for UjeebuClient.account method."""

    def setUp(self):
        self.client = UjeebuClient(api_key='test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_account(self, mock_get):
        """Test account method calls correct endpoint."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.account()

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertTrue(call_args[0][0].endswith('/account'))
        self.assertEqual(call_args.kwargs['params']['apiKey'], 'test_api_key')

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_account_uses_timeout(self, mock_get):
        """Test account uses client timeout."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        client = UjeebuClient(api_key='test_api_key', timeout=60)
        client.account()

        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['timeout'], 60)

    @patch('ujeebu_python.ujeebu_python.requests.get')
    def test_account_user_agent(self, mock_get):
        """Test account sends correct user-agent."""
        mock_response = MagicMock()
        mock_get.return_value = mock_response

        self.client.account()

        call_args = mock_get.call_args
        self.assertEqual(call_args.kwargs['headers']['user-agent'], 'Ujeebu-Python/0.1.4-beta')


if __name__ == '__main__':
    unittest.main()

