"""
Olostep Crawl Operator for Apache Airflow.

This operator crawls a website starting from a given URL using the Olostep API.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepCrawlOperator(BaseOperator):
    """
    Crawl a website using Olostep API.
    
    This operator starts a crawl job from a given URL, following links
    up to a specified maximum number of pages.
    
    :param url: Starting URL to crawl. Supports Jinja templating.
    :type url: str
    :param max_pages: Maximum number of pages to crawl. Default: 100.
    :type max_pages: int
    :param formats: Output formats for each page. Defaults to ['markdown'].
    :type formats: list[str]
    :param include_patterns: URL patterns to include (glob syntax, e.g., '/blog/**').
    :type include_patterns: list[str]
    :param exclude_patterns: URL patterns to exclude (glob syntax, e.g., '/admin/**').
    :type exclude_patterns: list[str]
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.crawl import OlostepCrawlOperator
        
        crawl_task = OlostepCrawlOperator(
            task_id="crawl_docs",
            url="https://docs.example.com",
            max_pages=50,
            include_patterns=["/docs/**", "/api/**"],
            exclude_patterns=["/docs/archive/**"],
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - url
        - formats
        - include_patterns
        - exclude_patterns
    """
    
    template_fields: Sequence[str] = ("url", "formats", "include_patterns", "exclude_patterns")
    template_ext: Sequence[str] = ()
    ui_color = "#e69138"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        url: str,
        max_pages: int = 100,
        formats: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepCrawlOperator."""
        super().__init__(**kwargs)
        self.url = url
        self.max_pages = max_pages
        self.formats = formats or ["markdown"]
        self.include_patterns = include_patterns
        self.exclude_patterns = exclude_patterns
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the crawl operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing crawl job info
        """
        self.log.info(f"Starting crawl from: {self.url}")
        self.log.info(f"Max pages: {self.max_pages}")
        self.log.info(f"Output formats: {self.formats}")
        
        if self.include_patterns:
            self.log.info(f"Include patterns: {self.include_patterns}")
        if self.exclude_patterns:
            self.log.info(f"Exclude patterns: {self.exclude_patterns}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        result = hook.crawl(
            url=self.url,
            max_pages=self.max_pages,
            formats=self.formats,
            include_patterns=self.include_patterns,
            exclude_patterns=self.exclude_patterns,
        )
        
        crawl_id = result.get("crawl_id") or result.get("id")
        self.log.info(f"Crawl job started with ID: {crawl_id}")
        
        # Store crawl_id in XCom for downstream tasks
        context["ti"].xcom_push(key="crawl_id", value=crawl_id)
        
        return result
