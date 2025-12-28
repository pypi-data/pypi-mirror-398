"""
Example DAG: Olostep Quick Start

A simple DAG demonstrating basic Olostep scraping operations.
This is a great starting point for learning the Olostep Airflow provider.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from airflow_provider_olostep.operators.scrape import OlostepScrapeOperator
from airflow_provider_olostep.operators.map import OlostepMapOperator
from airflow_provider_olostep.operators.ask import OlostepAskOperator


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="olostep_quickstart",
    default_args=default_args,
    description="Quick start example for Olostep web scraping",
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["olostep", "example", "quickstart"],
    doc_md="""
    # Olostep Quick Start DAG
    
    This DAG demonstrates basic Olostep operations:
    
    1. **Scrape Homepage** - Extract content from a website
    2. **Create Sitemap** - Discover all URLs on a site
    3. **Ask Question** - Get AI-powered answers about a page
    4. **Process Results** - Combine and analyze the data
    
    ## Usage
    
    1. Ensure you have an Airflow connection named `olostep_default` with your API key
    2. Trigger this DAG manually from the Airflow UI
    3. Check the task logs and XComs for results
    """,
) as dag:
    
    # Task 1: Scrape a single URL
    scrape_homepage = OlostepScrapeOperator(
        task_id="scrape_homepage",
        url="https://news.ycombinator.com",
        formats=["markdown", "text", "links"],
        wait_for=1000,  # Wait 1 second for page load
        doc_md="Scrape the Hacker News homepage and extract content in multiple formats.",
    )
    
    # Task 2: Create a sitemap of the website
    create_sitemap = OlostepMapOperator(
        task_id="create_sitemap",
        url="https://news.ycombinator.com",
        max_urls=20,  # Limit for demo purposes
        doc_md="Discover URLs on Hacker News (limited to 20 for demo).",
    )
    
    # Task 3: Ask a question about the page
    ask_about_page = OlostepAskOperator(
        task_id="ask_about_page",
        url="https://news.ycombinator.com",
        question="What are the top 3 stories on this page?",
        doc_md="Use AI to extract the top stories from the page.",
    )
    
    # Task 4: Process and summarize results
    def process_results(**context):
        """Combine results from all scraping tasks."""
        ti = context["ti"]
        
        # Get results from previous tasks
        scrape_result = ti.xcom_pull(task_ids="scrape_homepage")
        map_result = ti.xcom_pull(task_ids="create_sitemap")
        ask_result = ti.xcom_pull(task_ids="ask_about_page")
        
        # Calculate statistics
        markdown_length = len(scrape_result.get("markdown", ""))
        text_length = len(scrape_result.get("text", ""))
        links_count = len(scrape_result.get("links", []))
        urls_discovered = len(map_result.get("urls", []))
        answer = ask_result.get("answer", "No answer")
        
        summary = {
            "scraping": {
                "markdown_characters": markdown_length,
                "text_characters": text_length,
                "links_found": links_count,
            },
            "sitemap": {
                "urls_discovered": urls_discovered,
            },
            "qa": {
                "question": "What are the top 3 stories?",
                "answer": answer,
            },
        }
        
        print("=" * 60)
        print("OLOSTEP SCRAPING RESULTS SUMMARY")
        print("=" * 60)
        print(f"Markdown content: {markdown_length:,} characters")
        print(f"Text content: {text_length:,} characters")
        print(f"Links found: {links_count}")
        print(f"URLs discovered: {urls_discovered}")
        print(f"AI Answer: {answer[:200]}...")
        print("=" * 60)
        
        return summary
    
    summarize = PythonOperator(
        task_id="summarize_results",
        python_callable=process_results,
        doc_md="Combine and summarize all scraping results.",
    )
    
    # Define task dependencies
    # All scraping tasks run in parallel, then summarize
    [scrape_homepage, create_sitemap, ask_about_page] >> summarize
