"""
Olostep Batch Operator for Apache Airflow.

This operator batch scrapes multiple URLs using the Olostep API,
with optional waiting for completion.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepBatchOperator(BaseOperator):
    """
    Batch scrape multiple URLs using Olostep API.
    
    This operator submits multiple URLs for scraping in a single batch job.
    Optionally, it can wait for the batch to complete before returning.
    
    :param urls: List of URLs to scrape. Supports Jinja templating.
    :type urls: list[str]
    :param formats: Output formats for each URL. Defaults to ['markdown'].
    :type formats: list[str]
    :param wait_for_completion: If True, wait for the batch job to complete.
        If False (default), return immediately with batch job info.
    :type wait_for_completion: bool
    :param poll_interval: Seconds between status checks when waiting. Default: 10.
    :type poll_interval: int
    :param completion_timeout: Maximum seconds to wait for completion. Default: 3600 (1 hour).
    :type completion_timeout: int
    :param webhook_url: URL to call when batch completes (alternative to waiting).
    :type webhook_url: str
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.batch import OlostepBatchOperator
        
        # Fire and forget - returns immediately with batch ID
        batch_task = OlostepBatchOperator(
            task_id="batch_scrape",
            urls=["https://example.com/page1", "https://example.com/page2"],
            formats=["markdown"],
        )
        
        # Wait for completion - blocks until batch finishes
        batch_task_wait = OlostepBatchOperator(
            task_id="batch_scrape_wait",
            urls=["https://example.com/page1", "https://example.com/page2"],
            wait_for_completion=True,
            completion_timeout=1800,  # 30 minutes
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - urls
        - formats
        - webhook_url
    """
    
    template_fields: Sequence[str] = ("urls", "formats", "webhook_url")
    template_ext: Sequence[str] = ()
    ui_color = "#6aa84f"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        urls: List[str],
        formats: Optional[List[str]] = None,
        wait_for_completion: bool = False,
        poll_interval: int = 10,
        completion_timeout: int = 3600,
        webhook_url: Optional[str] = None,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepBatchOperator."""
        super().__init__(**kwargs)
        self.urls = urls
        self.formats = formats or ["markdown"]
        self.wait_for_completion = wait_for_completion
        self.poll_interval = poll_interval
        self.completion_timeout = completion_timeout
        self.webhook_url = webhook_url
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the batch scrape operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing batch job info or results if waited
        """
        self.log.info(f"Starting batch scrape for {len(self.urls)} URLs")
        self.log.info(f"Output formats: {self.formats}")
        self.log.info(f"Wait for completion: {self.wait_for_completion}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        # Start the batch job
        result = hook.batch_scrape(
            urls=self.urls,
            formats=self.formats,
            webhook_url=self.webhook_url,
        )
        
        batch_id = result.get("batch_id") or result.get("id")
        self.log.info(f"Batch job started with ID: {batch_id}")
        
        # Store batch_id in XCom for downstream tasks
        context["ti"].xcom_push(key="batch_id", value=batch_id)
        
        if self.wait_for_completion and batch_id:
            self.log.info(f"Waiting for batch {batch_id} to complete...")
            result = hook.wait_for_batch(
                batch_id=batch_id,
                poll_interval=self.poll_interval,
                timeout=self.completion_timeout,
            )
            
            # Log completion stats
            results_count = len(result.get("results", []))
            self.log.info(f"Batch {batch_id} completed with {results_count} results")
        
        return result
