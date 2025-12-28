"""
Olostep Answer Operator for Apache Airflow.

This operator performs AI-powered web search and returns structured answers.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence

from airflow.models import BaseOperator
from airflow.utils.context import Context

from airflow_provider_olostep.hooks.olostep import OlostepHook


class OlostepAnswerOperator(BaseOperator):
    """
    Search the web and get AI-powered answers using Olostep API.
    
    The AI performs intelligent web research to answer questions,
    browsing multiple sources and synthesizing information.
    Execution time is typically 3-30s depending on complexity.
    
    :param task: The question or research task to answer. Supports Jinja templating.
    :type task: str
    :param json_schema: Optional JSON schema for structured output.
    :type json_schema: dict
    :param olostep_conn_id: Airflow connection ID for Olostep API credentials.
    :type olostep_conn_id: str
    
    Example usage::
    
        from airflow_provider_olostep.operators.answer import OlostepAnswerOperator
        
        # Simple question
        answer_task = OlostepAnswerOperator(
            task_id="find_pricing",
            task="What is the latest pricing for Stripe?",
        )
        
        # Structured output
        structured_task = OlostepAnswerOperator(
            task_id="company_info",
            task="Find information about Tesla",
            json_schema={"ceo": "", "headquarters": "", "stock_price": ""},
        )
    
    Template fields::
    
        The following fields support Jinja templating:
        - task
    """
    
    template_fields: Sequence[str] = ("task",)
    template_ext: Sequence[str] = ()
    ui_color = "#674ea7"
    ui_fgcolor = "#ffffff"
    
    def __init__(
        self,
        *,
        task: str,
        json_schema: Optional[Dict[str, Any]] = None,
        olostep_conn_id: str = "olostep_default",
        **kwargs: Any,
    ) -> None:
        """Initialize the OlostepAnswerOperator."""
        super().__init__(**kwargs)
        self.task = task
        self.json_schema = json_schema
        self.olostep_conn_id = olostep_conn_id
    
    def execute(self, context: Context) -> dict:
        """
        Execute the answer operation.
        
        :param context: Airflow context dictionary
        :return: Dictionary containing the answer and sources
        """
        self.log.info(f"Searching web for: {self.task}")
        
        hook = OlostepHook(olostep_conn_id=self.olostep_conn_id)
        
        result = hook.answer(
            task=self.task,
            json_schema=self.json_schema,
        )
        
        # Extract answer content
        result_data = result.get("result", {})
        markdown_content = result_data.get("markdown_content", "")
        json_content = result_data.get("json_content")
        
        if markdown_content:
            self.log.info(f"Answer received: {markdown_content[:200]}...")
        elif json_content:
            self.log.info(f"Structured answer received: {str(json_content)[:200]}...")
        
        # Store in XCom for downstream tasks
        context["ti"].xcom_push(key="markdown_content", value=markdown_content)
        if json_content:
            context["ti"].xcom_push(key="json_content", value=json_content)
        
        return result
