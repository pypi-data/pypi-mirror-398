"""
Olostep Map Operator for Apache Airflow.

This operator creates a sitemap of a website by discovering all URLs using the Olostep API.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepMapOperator(BaseOperator):
    """
    Create a sitemap of a website using Olostep API.
    
    This operator discovers all URLs on a website, optionally filtered
    by include/exclude patterns. This is useful for discovering pages
    before batch scraping.
    
    :param url: Website URL to map. Supports Jinja templating.
    :type url: str
    :param include_patterns: URL patterns to include (glob syntax).
    :type include_patterns: list[str]
    :param exclude_patterns: URL patterns to exclude (glob syntax).
    :type exclude_patterns: list[str]
    :param max_urls: Maximum number of URLs to discover.
    :type max_urls: int
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.map import OlostepMapOperator
        
        map_task = OlostepMapOperator(
            task_id="discover_product_pages",
            url="https://shop.example.com",
            include_patterns=["/products/**"],
            exclude_patterns=["/products/archived/**"],
            max_urls=500,
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - url
        - include_patterns
        - exclude_patterns
    """
    
    template_fields: Sequence[str] = ("url", "include_patterns", "exclude_patterns")
    template_ext: Sequence[str] = ()
    ui_color = "#9fc5e8"
    ui_fgcolor = "#000000"
    
    def __init__(
        self,
        *,
        url: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        max_urls: Optional[int] = None,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepMapOperator."""
        super().__init__(**kwargs)
        self.url = url
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.max_urls = max_urls
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the map operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing discovered URLs and metadata
        """
        self.log.info(f"Creating sitemap for: {self.url}")
        
        if self.include_patterns:
            self.log.info(f"Include patterns: {self.include_patterns}")
        if self.exclude_patterns:
            self.log.info(f"Exclude patterns: {self.exclude_patterns}")
        if self.max_urls:
            self.log.info(f"Max URLs: {self.max_urls}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        result = hook.create_map(
            url=self.url,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
            max_urls=self.max_urls,
        )
        
        urls = result.get("urls", [])
        self.log.info(f"Discovered {len(urls)} URLs")
        
        # Store URLs in XCom for downstream tasks
        context["ti"].xcom_push(key="urls", value=urls)
        context["ti"].xcom_push(key="url_count", value=len(urls))
        
        return result
