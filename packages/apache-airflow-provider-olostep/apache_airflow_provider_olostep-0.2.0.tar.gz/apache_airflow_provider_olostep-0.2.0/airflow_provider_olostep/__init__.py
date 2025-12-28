"""
Apache Airflow Provider for Olostep Web Scraping API.

This provider enables seamless integration between Apache Airflow and Olostep's
web scraping and data extraction API, allowing you to build powerful data pipelines
for web content collection and processing.

Available components:
- OlostepHook: Connection management for Olostep API
- OlostepScrapeOperator: Scrape single URLs
- OlostepBatchOperator: Batch scrape multiple URLs
- OlostepCrawlOperator: Crawl websites
- OlostepMapOperator: Create sitemaps
- OlostepBatchSensor: Wait for batch jobs to complete
"""

__version__ = "0.2.0"


def get_provider_info() -> dict:
    """
    Return provider metadata for Apache Airflow.
    
    This function is called by Airflow to discover provider information,
    connection types, and available components.
    """
    return {
        "package-name": "apache-airflow-provider-olostep",
        "name": "Olostep",
        "description": "Apache Airflow provider for Olostep web scraping and data extraction API.",
        "connection-types": [
            {
                "connection-type": "olostep",
                "hook-class-name": "airflow_provider_olostep.hooks.olostep.OlostepHook",
            }
        ],
        "extra-links": [],
        "versions": [__version__],
    }
