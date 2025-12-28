"""
Olostep Hook for Apache Airflow.

This hook manages connections to the Olostep API and provides methods
for all available API operations including scraping, batch processing,
crawling, and sitemap generation.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from airflow.hooks.base import BaseHook


class OlostepHook(BaseHook):
    """
    Hook to interact with Olostep Web Scraping API.
    
    This hook provides methods to scrape web pages, batch process multiple URLs,
    crawl websites, and create sitemaps using the Olostep API.
    
    :param olostep_conn_id: The connection ID to use when fetching connection info.
        The connection should have the API key stored as the password field.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.hooks.olostep import OlostepHook
        
        hook = OlostepHook(olostep_conn_id='olostep_default')
        result = hook.scrape(url='https://example.com', formats=['markdown'])
    """
    
    conn_name_attr = "olostep_conn_id"
    default_conn_name = "olostep_default"
    conn_type = "olostep"
    hook_name = "Olostep"
    
    BASE_URL = "https://api.olostep.com/v1"
    
    # Connection form fields for Airflow UI
    @staticmethod
    def get_connection_form_widgets() -> Dict[str, Any]:
        """Return connection form widgets for the Airflow UI."""
        from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
        from flask_babel import lazy_gettext
        from wtforms import StringField
        
        return {
            "base_url": StringField(
                lazy_gettext("API Base URL"),
                widget=BS3TextFieldWidget(),
                description="Override the default Olostep API URL (optional)",
            ),
        }
    
    @staticmethod
    def get_ui_field_behaviour() -> Dict[str, Any]:
        """Return custom field behavior for the Airflow connection UI."""
        return {
            "hidden_fields": ["host", "port", "login", "schema"],
            "relabeling": {
                "password": "API Key",
            },
            "placeholders": {
                "password": "Enter your Olostep API key",
                "extra": '{"base_url": "https://api.olostep.com/v1"}',
            },
        }
    
    def __init__(self, olostep_conn_id: str = default_conn_name) -> None:
        """
        Initialize the Olostep Hook.
        
        :param olostep_conn_id: Connection ID for Olostep API credentials
        """
        super().__init__()
        self.olostep_conn_id = olostep_conn_id
        self._api_key: Optional[str] = None
        self._base_url: Optional[str] = None
        self._session: Optional[requests.Session] = None
    
    @property
    def api_key(self) -> str:
        """
        Get API key from Airflow connection.
        
        :return: The Olostep API key
        :raises ValueError: If no API key is found in the connection
        """
        if self._api_key is None:
            conn = self.get_connection(self.olostep_conn_id)
            self._api_key = conn.password
            
            # Also check extra JSON for api_key
            if not self._api_key:
                extra = conn.extra_dejson or {}
                self._api_key = extra.get("api_key")
            
            if not self._api_key:
                raise ValueError(
                    f"No API key found in connection '{self.olostep_conn_id}'. "
                    "Please set the API key in the password field or in the extra JSON as 'api_key'."
                )
            
            # Check for custom base URL
            extra = conn.extra_dejson or {}
            if "base_url" in extra:
                self._base_url = extra["base_url"]
        
        return self._api_key
    
    @property
    def base_url(self) -> str:
        """Get the API base URL."""
        if self._base_url is None:
            # Trigger api_key property to load connection details
            _ = self.api_key
        return self._base_url or self.BASE_URL
    
    @property
    def session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self._get_headers())
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get request headers with authentication.
        
        :return: Dictionary of HTTP headers
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"airflow-provider-olostep/{__import__('airflow_provider_olostep').__version__}",
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the Olostep API.
        
        :param method: HTTP method (GET, POST, etc.)
        :param endpoint: API endpoint (e.g., '/scrapes')
        :param payload: Request payload for POST requests
        :param timeout: Request timeout in seconds
        :return: JSON response as dictionary
        :raises requests.HTTPError: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        self.log.debug(f"Making {method} request to {url}")
        
        response = self.session.request(
            method=method,
            url=url,
            json=payload,
            timeout=timeout,
        )
        
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            self.log.error(f"Olostep API error: {response.text}")
            raise
        
        return response.json()
    
    def scrape(
        self,
        url: str,
        formats: Optional[List[str]] = None,
        wait_for: Optional[int] = None,
        country: Optional[str] = None,
        remove_selectors: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Scrape a single URL.
        
        :param url: URL to scrape
        :param formats: Output formats (markdown, html, text, screenshot, etc.)
        :param wait_for: Milliseconds to wait before scraping (for JS rendering)
        :param country: Country code for geo-targeted requests
        :param remove_selectors: CSS selectors to remove from the page
        :param kwargs: Additional API parameters
        :return: Scraped content and metadata
        
        Example::
        
            result = hook.scrape(
                url="https://example.com",
                formats=["markdown", "text"],
                wait_for=2000,
            )
        """
        payload: Dict[str, Any] = {
            "url_to_scrape": url,
            "formats": formats or ["markdown"],
        }
        
        if wait_for is not None:
            payload["wait_for"] = wait_for
        if country is not None:
            payload["country"] = country
        if remove_selectors is not None:
            payload["remove_selectors"] = remove_selectors
        
        payload.update(kwargs)
        
        self.log.info(f"Scraping URL: {url}")
        result = self._make_request("POST", "/scrapes", payload)
        self.log.info(f"Successfully scraped {url}")
        
        return result
    
    def batch_scrape(
        self,
        urls: List[str],
        formats: Optional[List[str]] = None,
        webhook_url: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Batch scrape multiple URLs.
        
        :param urls: List of URLs to scrape
        :param formats: Output formats
        :param webhook_url: URL to call when batch completes
        :param kwargs: Additional API parameters
        :return: Batch job information including batch_id
        
        Example::
        
            result = hook.batch_scrape(
                urls=["https://example.com/page1", "https://example.com/page2"],
                formats=["markdown"],
            )
            batch_id = result.get("batch_id") or result.get("id")
        """
        payload: Dict[str, Any] = {
            "urls": urls,
            "formats": formats or ["markdown"],
        }
        
        if webhook_url is not None:
            payload["webhook_url"] = webhook_url
        
        payload.update(kwargs)
        
        self.log.info(f"Starting batch scrape for {len(urls)} URLs")
        result = self._make_request("POST", "/batches", payload, timeout=60)
        
        batch_id = result.get("batch_id") or result.get("id")
        self.log.info(f"Batch job created with ID: {batch_id}")
        
        return result
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get status of a batch job.
        
        :param batch_id: The batch job ID
        :return: Batch status and results if complete
        """
        self.log.debug(f"Checking status of batch {batch_id}")
        return self._make_request("GET", f"/batches/{batch_id}", timeout=30)
    
    def wait_for_batch(
        self,
        batch_id: str,
        poll_interval: int = 10,
        timeout: int = 3600,
    ) -> Dict[str, Any]:
        """
        Wait for a batch job to complete.
        
        :param batch_id: The batch job ID
        :param poll_interval: Seconds between status checks
        :param timeout: Maximum seconds to wait
        :return: Final batch status and results
        :raises TimeoutError: If the batch doesn't complete within timeout
        :raises RuntimeError: If the batch job fails
        """
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Batch {batch_id} did not complete within {timeout} seconds")
            
            status = self.get_batch_status(batch_id)
            state = status.get("status", "unknown").lower()
            
            self.log.info(f"Batch {batch_id} status: {state} (elapsed: {int(elapsed)}s)")
            
            if state in ("completed", "finished", "done"):
                return status
            elif state in ("failed", "error"):
                raise RuntimeError(f"Batch job {batch_id} failed: {status}")
            
            time.sleep(poll_interval)
    
    def crawl(
        self,
        url: str,
        max_pages: int = 100,
        formats: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Start a crawl job.
        
        :param url: Starting URL to crawl
        :param max_pages: Maximum pages to crawl
        :param formats: Output formats
        :param include_patterns: URL patterns to include (glob syntax)
        :param exclude_patterns: URL patterns to exclude (glob syntax)
        :param kwargs: Additional API parameters
        :return: Crawl job information
        
        Example::
        
            result = hook.crawl(
                url="https://example.com",
                max_pages=50,
                include_patterns=["/blog/**", "/docs/**"],
                exclude_patterns=["/admin/**"],
            )
        """
        payload: Dict[str, Any] = {
            "url": url,
            "max_pages": max_pages,
            "formats": formats or ["markdown"],
        }
        
        if include_patterns is not None:
            payload["include_patterns"] = include_patterns
        if exclude_patterns is not None:
            payload["exclude_patterns"] = exclude_patterns
        
        payload.update(kwargs)
        
        self.log.info(f"Starting crawl from {url} (max {max_pages} pages)")
        result = self._make_request("POST", "/crawls", payload, timeout=60)
        self.log.info(f"Crawl job started: {result.get('crawl_id') or result.get('id')}")
        
        return result
    
    def get_crawl_status(self, crawl_id: str) -> Dict[str, Any]:
        """
        Get status of a crawl job.
        
        :param crawl_id: The crawl job ID
        :return: Crawl status and results
        """
        return self._make_request("GET", f"/crawls/{crawl_id}", timeout=30)
    
    def create_map(
        self,
        url: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_urls: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Create a sitemap of a website.
        
        :param url: Website URL to map
        :param include_patterns: URL patterns to include
        :param exclude_patterns: URL patterns to exclude
        :param max_urls: Maximum URLs to discover
        :param kwargs: Additional API parameters
        :return: Map results with discovered URLs
        
        Example::
        
            result = hook.create_map(
                url="https://example.com",
                include_patterns=["/products/**"],
                max_urls=1000,
            )
            urls = result.get("urls", [])
        """
        payload: Dict[str, Any] = {"url": url}
        
        if include_patterns is not None:
            payload["include_patterns"] = include_patterns
        if exclude_patterns is not None:
            payload["exclude_patterns"] = exclude_patterns
        if max_urls is not None:
            payload["max_urls"] = max_urls
        
        payload.update(kwargs)
        
        self.log.info(f"Creating sitemap for {url}")
        result = self._make_request("POST", "/maps", payload, timeout=120)
        
        urls_found = len(result.get("urls", []))
        self.log.info(f"Sitemap created with {urls_found} URLs")
        
        return result
    
    def ask(
        self,
        url: str,
        question: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Ask a question about a webpage.
        
        :param url: URL to analyze
        :param question: Question to answer based on page content
        :param kwargs: Additional API parameters
        :return: Answer and supporting content
        
        Example::
        
            result = hook.ask(
                url="https://example.com/pricing",
                question="What are the pricing tiers?",
            )
            answer = result.get("answer")
        """
        payload: Dict[str, Any] = {
            "url": url,
            "question": question,
        }
        payload.update(kwargs)
        
        self.log.info(f"Asking question about {url}: {question[:50]}...")
        result = self._make_request("POST", "/ask", payload, timeout=60)
        
        return result
    
    def test_connection(self) -> Tuple[bool, str]:
        """
        Test the Olostep API connection.
        
        This method is used by Airflow's connection testing feature.
        
        :return: Tuple of (success, message)
        """
        try:
            # Use a simple, fast request to test connectivity
            self.scrape("https://example.com", formats=["text"])
            return True, "Successfully connected to Olostep API"
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                return False, "Authentication failed: Invalid API key"
            elif e.response.status_code == 403:
                return False, "Authorization failed: API key lacks permissions"
            return False, f"HTTP error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
