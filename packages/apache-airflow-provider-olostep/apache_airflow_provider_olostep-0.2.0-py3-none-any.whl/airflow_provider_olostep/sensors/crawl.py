"""
Olostep Crawl Sensor for Apache Airflow.

This sensor waits for an Olostep crawl job to complete.
"""

from __future__ import annotations

from typing import Any, Sequence

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepCrawlSensor(BaseSensorOperator):
    """
    Wait for an Olostep crawl job to complete.
    
    This sensor polls the Olostep API to check if a crawl job has finished.
    
    :param crawl_id: The crawl job ID to monitor. Supports Jinja templating.
    :type crawl_id: str
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.crawl import OlostepCrawlOperator
        from airflow_provider_olostep.sensors.crawl import OlostepCrawlSensor
        
        # Start crawl job
        crawl_task = OlostepCrawlOperator(
            task_id="start_crawl",
            url="https://docs.example.com",
            max_pages=100,
        )
        
        # Wait for completion
        wait_task = OlostepCrawlSensor(
            task_id="wait_for_crawl",
            crawl_id="{{ ti.xcom_pull(task_ids='start_crawl', key='crawl_id') }}",
            poke_interval=60,
            timeout=7200,
            mode="reschedule",
        )
        
        crawl_task >> wait_task
    
    Template fields::
    
        The following fields support Jinja templating:
        - crawl_id
    """
    
    template_fields: Sequence[str] = ("crawl_id",)
    ui_color = "#e69138"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        crawl_id: str,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepCrawlSensor."""
        super().__init__(**kwargs)
        self.crawl_id = crawl_id
        self.olostep_conn_id = olostep_conn_id
    
    def poke(self, context: Context) -> bool:
        """
        Check if the crawl job has completed.
        
        :param context: Airflow context dictionary
        :return: True if crawl completed, False otherwise
        :raises RuntimeError: If the crawl job failed
        """
        self.log.info(f"Checking status of crawl: {self.crawl_id}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        status = hook.get_crawl_status(self.crawl_id)
        
        state = status.get("status", "unknown").lower()
        pages_crawled = status.get("pages_crawled", 0)
        
        self.log.info(f"Crawl {self.crawl_id} status: {state} ({pages_crawled} pages)")
        
        if state in ("failed", "error"):
            error_msg = status.get("error", "Unknown error")
            raise RuntimeError(f"Crawl job {self.crawl_id} failed: {error_msg}")
        
        if state in ("completed", "finished", "done"):
            context["ti"].xcom_push(key="crawl_results", value=status)
            return True
        
        return False
