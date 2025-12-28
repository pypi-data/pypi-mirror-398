"""
Olostep Scrape Operator for Apache Airflow.

This operator scrapes a single URL using the Olostep API and returns
the extracted content in the specified formats.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepScrapeOperator(BaseOperator):
    """
    Scrape a URL using Olostep API.
    
    This operator fetches content from a single URL and extracts it in
    the specified formats (markdown, HTML, text, screenshot, etc.).
    
    :param url: URL to scrape. Supports Jinja templating.
    :type url: str
    :param formats: Output formats. Options: markdown, html, text, screenshot, json, links.
        Defaults to ['markdown'].
    :type formats: list[str]
    :param wait_for: Milliseconds to wait before scraping (for JavaScript rendering).
    :type wait_for: int
    :param country: Country code for geo-targeted requests (e.g., 'US', 'GB', 'DE').
    :type country: str
    :param remove_selectors: CSS selectors to remove from the page before extraction.
    :type remove_selectors: list[str]
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.scrape import OlostepScrapeOperator
        
        scrape_task = OlostepScrapeOperator(
            task_id="scrape_homepage",
            url="https://example.com",
            formats=["markdown", "text"],
            wait_for=2000,  # Wait 2 seconds for JS
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - url
        - formats
        - country
    """
    
    template_fields: Sequence[str] = ("url", "formats", "country")
    template_ext: Sequence[str] = ()
    ui_color = "#3d85c6"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        url: str,
        formats: Optional[List[str]] = None,
        wait_for: Optional[int] = None,
        country: Optional[str] = None,
        remove_selectors: Optional[List[str]] = None,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepScrapeOperator."""
        super().__init__(**kwargs)
        self.url = url
        self.formats = formats or ["markdown"]
        self.wait_for = wait_for
        self.country = country
        self.remove_selectors = remove_selectors
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the scrape operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing scraped content and metadata
        """
        self.log.info(f"Scraping URL: {self.url}")
        self.log.info(f"Output formats: {self.formats}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        result = hook.scrape(
            url=self.url,
            formats=self.formats,
            wait_for=self.wait_for,
            country=self.country,
            remove_selectors=self.remove_selectors,
        )
        
        # Log some metrics
        if "markdown" in result:
            self.log.info(f"Markdown content length: {len(result.get('markdown', ''))}")
        if "text" in result:
            self.log.info(f"Text content length: {len(result.get('text', ''))}")
        
        self.log.info(f"Successfully scraped {self.url}")
        return result
