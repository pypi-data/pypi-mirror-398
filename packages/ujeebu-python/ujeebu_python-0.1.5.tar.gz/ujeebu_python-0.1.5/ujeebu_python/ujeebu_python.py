import json
import urllib
import requests
from . import __version__
USER_AGENT = f"Ujeebu-Python/{__version__}"
class UjeebuClient:
    def __init__(self, api_key=None, base_url=None, timeout=120):
        if not api_key:
            raise ValueError("api_key is required")
        self.base_url = base_url or 'https://api.ujeebu.com'
        self.api_key = api_key
        self.timeout = timeout
    def extract(self, url, params={}, headers=None):
        headers = headers or {}
        has_raw_html = None
        if 'raw_html' in params:
            has_raw_html = len(params['raw_html']) > 0
        headers = self.handle_headers(headers)
        if has_raw_html:
            headers['apiKey'] = self.api_key
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
            return requests.post(self.base_url + '/extract', data={
                **params,
                **{
                    "url": url,
                }
            }, headers={
                **headers,
                **{"user-agent": USER_AGENT}
            }, timeout=self.timeout)
        params = self.handle_ujeebu_params({
            **{"url": url},
            **params
        })
        return requests.get(self.base_url + '/extract', params={
            **params,
            **{"apiKey": self.api_key}
        }, headers={
            **headers,
            **{"user-agent": USER_AGENT}
        })
    def scrape(self, url, params={}, headers=None):
        headers = headers or {}
        has_extract_rules = False
        if 'extract_rules' in params:
            has_extract_rules = bool(params['extract_rules'])
        headers = self.handle_headers(headers)
        if has_extract_rules:
            return requests.post(self.base_url + '/scrape', data=json.dumps({
                **{"url": url},
                **params
            }), headers={
                **{
                    "apiKey": self.api_key,
                    "user-agent": USER_AGENT,
                    "Content-Type": "application/json"
                },
                **headers
            })
        params = self.handle_ujeebu_params({
            **{"url": url, "apikey": self.api_key},
            **params
        })
        return requests.get(self.base_url + '/scrape', params=params, headers={
            **headers,
            **{"user-agent": USER_AGENT}
        })
    def serp(self, params={}, headers=None):
        headers = headers or {}
        headers = self.handle_headers(headers)
        params = self.handle_ujeebu_params(params)
        return requests.get(self.base_url + '/serp', params={
            **params,
            **{"apiKey": self.api_key}
        }, headers={
            **headers,
            **{"user-agent": USER_AGENT}
        })
    def preview(self, url, params={}, headers=None):
        headers = headers or {}
        headers = self.handle_headers(headers)
        params = self.handle_ujeebu_params({
            **params,
            **{
                "url": url,
                "apikey": self.api_key
            }
        })
        return requests.get(self.base_url + '/card', params=params, headers={
            **headers,
            **{"user-agent": USER_AGENT}
        }, timeout=self.timeout)
    @staticmethod
    def handle_url(url):
        return url
        # return urllib.parse.quote_plus(url)
    @staticmethod
    def handle_custom_js(js):
        return urllib.parse.quote_plus(js)
        # return base64.b64encode(s.encode()).decode()
    @staticmethod
    def handle_headers(headers):
        if headers is None:
            return None
        return {f'Ujb-{k}': v for k, v in headers.items()}
    @staticmethod
    def handle_cookies(cookies):
        if cookies is None:
            return None
        if isinstance(cookies, dict):
            str_cookies = ';'.join(f'{k}={v}' for k, v in cookies.items())
            return urllib.parse.quote(str_cookies)
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
                new_params[k] = v
            elif k == 'url':
                new_params[k] = cls.handle_url(v)
            elif k == 'custom_js':
                new_params[k] = cls.handle_custom_js(v)
            elif k == 'screenshot_partial' and isinstance(v, dict):
                new_params[k] = json.dumps(v)
            elif k == 'cookies':
                new_params[k] = cls.handle_cookies(v)
            else:
                new_params[k] = v
        return new_params
    # Scrape helper methods
    def get_pdf(self, url, params=None, headers=None):
        """
        Gets a PDF of a web page using the Scrape API.
        Args:
            url (str): The URL to create a PDF from
            params (dict, optional): Additional parameters for the PDF generation
            headers (dict, optional): Headers to forward to the request
        Returns:
            requests.Response: Response object containing the PDF data
        """
        params = params or {}
        return self.scrape(url, {
            **params,
            'response_type': 'pdf',
            'json': True
        }, headers)
    def get_screenshot(self, url, params=None, headers=None):
        """
        Gets a screenshot of a web page using the Scrape API.
        Args:
            url (str): The URL to take a screenshot of
            params (dict, optional): Additional parameters for the screenshot
            headers (dict, optional): Headers to forward to the request
        Returns:
            requests.Response: Response object containing the screenshot data
        """
        params = params or {}
        return self.scrape(url, {
            **params,
            'response_type': 'screenshot',
            'json': True
        }, headers)
    def scrape_with_rules(self, url, extract_rules, params=None, headers=None):
        """
        Extracts data from a web page using extraction rules with the Scrape API.
        Args:
            url (str): The URL to extract data from
            extract_rules (dict): The rules to extract data with
            params (dict, optional): Additional parameters for the extraction
            headers (dict, optional): Headers to forward to the request
        Returns:
            requests.Response: Response object containing the extracted data
        """
        params = params or {}
        return self.scrape(url, {
            **params,
            'extract_rules': extract_rules,
            'json': True
        }, headers)
    def get_html(self, url, params=None, headers=None):
        """
        Gets the HTML of a web page using the Scrape API.
        Args:
            url (str): The URL to get HTML from
            params (dict, optional): Additional parameters for the request
            headers (dict, optional): Headers to forward to the request
        Returns:
            requests.Response: Response object containing the HTML data
        """
        params = params or {}
        return self.scrape(url, {
            **params,
            'response_type': 'html',
            'json': True
        }, headers)
    # SERP helper methods
    def search_text(self, search, params=None):
        """
        Performs a Google text search using the SERP API.
        Args:
            search (str): The search query to perform on Google
            params (dict, optional): Additional parameters for the search
        Returns:
            requests.Response: Response object containing search results
        """
        params = params or {}
        return self.serp({
            **params,
            'search': search,
            'search_type': 'search'
        })
    def search_news(self, search, params=None):
        """
        Performs a Google news search using the SERP API.
        Args:
            search (str): The search query to perform on Google News
            params (dict, optional): Additional parameters for the search
        Returns:
            requests.Response: Response object containing news results
        """
        params = params or {}
        return self.serp({
            **params,
            'search': search,
            'search_type': 'news'
        })
    def search_images(self, search, params=None):
        """
        Performs a Google images search using the SERP API.
        Args:
            search (str): The search query to perform on Google Images
            params (dict, optional): Additional parameters for the search
        Returns:
            requests.Response: Response object containing image results
        """
        params = params or {}
        return self.serp({
            **params,
            'search': search,
            'search_type': 'images'
        })
    def search_videos(self, search, params=None):
        """
        Performs a Google videos search using the SERP API.
        Args:
            search (str): The search query to perform on Google Videos
            params (dict, optional): Additional parameters for the search
        Returns:
            requests.Response: Response object containing video results
        """
        params = params or {}
        return self.serp({
            **params,
            'search': search,
            'search_type': 'videos'
        })
    def search_maps(self, search, params=None):
        """
        Performs a Google Maps search using the SERP API.
        Args:
            search (str): The search query to perform on Google Maps
            params (dict, optional): Additional parameters for the search
        Returns:
            requests.Response: Response object containing maps results
        """
        params = params or {}
        return self.serp({
            **params,
            'search': search,
            'search_type': 'maps'
        })
    # Account endpoint
    def account(self):
        """
        Retrieves account details using the Account API.
        Returns:
            requests.Response: Response object containing account information
        """
        return requests.get(
            self.base_url + '/account',
            params={'apiKey': self.api_key},
            headers={'user-agent': USER_AGENT},
            timeout=self.timeout
        )
