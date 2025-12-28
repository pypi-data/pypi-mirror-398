"""
Olostep Ask Operator for Apache Airflow.

This operator asks a question about a webpage and returns an AI-generated answer.
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepAskOperator(BaseOperator):
    """
    Ask a question about a webpage using Olostep API.
    
    This operator analyzes a webpage and answers a question based on its content.
    Useful for extracting specific information without parsing the full page.
    
    :param url: URL to analyze. Supports Jinja templating.
    :type url: str
    :param question: Question to answer based on page content. Supports Jinja templating.
    :type question: str
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.ask import OlostepAskOperator
        
        ask_task = OlostepAskOperator(
            task_id="get_pricing",
            url="https://example.com/pricing",
            question="What is the price of the enterprise plan?",
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - url
        - question
    """
    
    template_fields: Sequence[str] = ("url", "question")
    template_ext: Sequence[str] = ()
    ui_color = "#674ea7"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        url: str,
        question: str,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepAskOperator."""
        super().__init__(**kwargs)
        self.url = url
        self.question = question
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the ask operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing the answer and supporting content
        """
        self.log.info(f"Asking question about: {self.url}")
        self.log.info(f"Question: {self.question}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        result = hook.ask(
            url=self.url,
            question=self.question,
        )
        
        answer = result.get("answer", "")
        self.log.info(f"Answer received: {answer[:200]}...")
        
        # Store answer in XCom
        context["ti"].xcom_push(key="answer", value=answer)
        
        return result
