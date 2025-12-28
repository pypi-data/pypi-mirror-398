"""
Olostep Batch Sensor for Apache Airflow.

This sensor waits for an Olostep batch job to complete.
"""

from __future__ import annotations

from typing import Any, Sequence

from airflow.sensors.base import BaseSensorOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepBatchSensor(BaseSensorOperator):
    """
    Wait for an Olostep batch job to complete.
    
    This sensor polls the Olostep API to check if a batch job has finished.
    It's useful when you start a batch job in one task and need to wait
    for completion before proceeding.
    
    :param batch_id: The batch job ID to monitor. Supports Jinja templating.
    :type batch_id: str
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.batch import OlostepBatchOperator
        from airflow_provider_olostep.sensors.batch import OlostepBatchSensor
        
        # Start batch job
        batch_task = OlostepBatchOperator(
            task_id="start_batch",
            urls=["https://example.com/page1", "https://example.com/page2"],
        )
        
        # Wait for completion using sensor
        wait_task = OlostepBatchSensor(
            task_id="wait_for_batch",
            batch_id="{{ ti.xcom_pull(task_ids='start_batch', key='batch_id') }}",
            poke_interval=30,  # Check every 30 seconds
            timeout=3600,  # Timeout after 1 hour
            mode="reschedule",  # Free up worker while waiting
        )
        
        batch_task >> wait_task
    
    Template fields::
    
        The following fields support Jinja templating:
        - batch_id
    """
    
    template_fields: Sequence[str] = ("batch_id",)
    ui_color = "#6aa84f"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        batch_id: str,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepBatchSensor."""
        super().__init__(**kwargs)
        self.batch_id = batch_id
        self.olostep_conn_id = olostep_conn_id
    
    def poke(self, context: Context) -> bool:
        """
        Check if the batch job has completed.
        
        :param context: Airflow context dictionary
        :return: True if batch completed, False otherwise
        :raises RuntimeError: If the batch job failed
        """
        self.log.info(f"Checking status of batch: {self.batch_id}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        status = hook.get_batch_status(self.batch_id)
        
        state = status.get("status", "unknown").lower()
        progress = status.get("progress", {})
        completed = progress.get("completed", 0)
        total = progress.get("total", 0)
        
        self.log.info(f"Batch {self.batch_id} status: {state} ({completed}/{total})")
        
        if state in ("failed", "error"):
            error_msg = status.get("error", "Unknown error")
            raise RuntimeError(f"Batch job {self.batch_id} failed: {error_msg}")
        
        if state in ("completed", "finished", "done"):
            # Store results in XCom for downstream tasks
            context["ti"].xcom_push(key="batch_results", value=status)
            return True
        
        return False
