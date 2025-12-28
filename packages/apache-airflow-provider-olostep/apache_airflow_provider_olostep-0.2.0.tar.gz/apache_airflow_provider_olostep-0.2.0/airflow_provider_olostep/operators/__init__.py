"""Olostep Operators for Apache Airflow."""

from airflow_provider_olostep.operators.scrape import OlostepScrapeOperator
from airflow_provider_olostep.operators.batch import OlostepBatchOperator
from airflow_provider_olostep.operators.crawl import OlostepCrawlOperator
from airflow_provider_olostep.operators.map import OlostepMapOperator
from airflow_provider_olostep.operators.answer import OlostepAnswerOperator

# Backward compatibility alias
OlostepAskOperator = OlostepAnswerOperator

__all__ = [
    "OlostepScrapeOperator",
    "OlostepBatchOperator",
    "OlostepCrawlOperator",
    "OlostepMapOperator",
    "OlostepAnswerOperator",
    "OlostepAskOperator",  # Deprecated alias
]
