"""
Example DAG: E-commerce Product Monitoring Pipeline

A production-ready DAG that monitors competitor product prices by:
1. Discovering product pages on competitor websites
2. Batch scraping product information
3. Extracting structured pricing data
4. Saving results for analysis

This is a realistic use case for web scraping in data pipelines.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator

from airflow_provider_olostep.operators.map import OlostepMapOperator
from airflow_provider_olostep.operators.batch import OlostepBatchOperator
from airflow_provider_olostep.hooks.olostep import OlostepHook


default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "email_on_failure": True,
    "email": ["alerts@example.com"],
    "retries": 2,
    "retry_delay": timedelta(minutes=10),
    "execution_timeout": timedelta(hours=2),
}


# Configuration - could be moved to Airflow Variables
COMPETITOR_SITES = [
    {
        "name": "competitor_a",
        "url": "https://books.toscrape.com",  # Demo site for scraping
        "product_pattern": "/catalogue/**",
        "exclude_pattern": "/catalogue/category/**",
    },
]


with DAG(
    dag_id="ecommerce_product_monitor",
    default_args=default_args,
    description="Monitor competitor product prices daily",
    schedule_interval="0 6 * * *",  # Run daily at 6 AM
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["olostep", "ecommerce", "monitoring", "production"],
    doc_md="""
    # E-commerce Product Monitoring Pipeline
    
    This DAG monitors competitor websites for product pricing changes.
    
    ## Pipeline Steps
    
    1. **Discover Products** - Find all product pages on competitor sites
    2. **Filter & Prioritize** - Select pages to scrape (new/changed)
    3. **Batch Scrape** - Extract product page content
    4. **Extract Pricing** - Parse structured pricing data
    5. **Save Results** - Store in data warehouse
    
    ## Configuration
    
    Modify the `COMPETITOR_SITES` list to add more competitors.
    
    ## Monitoring
    
    - Check the `products_scraped` metric in task logs
    - Alerts are sent to data-team on failure
    """,
) as dag:
    
    start = EmptyOperator(task_id="start")
    
    # Task 1: Discover product pages on competitor site
    discover_products = OlostepMapOperator(
        task_id="discover_product_pages",
        url=COMPETITOR_SITES[0]["url"],
        include_patterns=[COMPETITOR_SITES[0]["product_pattern"]],
        exclude_patterns=[COMPETITOR_SITES[0]["exclude_pattern"]],
        max_urls=200,  # Limit for cost control
        doc_md="Discover all product pages on the competitor site.",
    )
    
    # Task 2: Check if there are products to scrape
    def check_products_found(**context) -> str:
        """Branch based on whether products were found."""
        ti = context["ti"]
        urls = ti.xcom_pull(task_ids="discover_product_pages", key="urls") or []
        
        if len(urls) > 0:
            print(f"Found {len(urls)} product pages to scrape")
            return "batch_scrape_products"
        else:
            print("No product pages found, skipping scrape")
            return "no_products_found"
    
    branch = BranchPythonOperator(
        task_id="check_products_found",
        python_callable=check_products_found,
    )
    
    no_products = EmptyOperator(
        task_id="no_products_found",
        doc_md="No products found - pipeline ends here.",
    )
    
    # Task 3: Batch scrape all product pages
    def batch_scrape_products(**context):
        """Scrape all discovered product pages."""
        ti = context["ti"]
        urls = ti.xcom_pull(task_ids="discover_product_pages", key="urls") or []
        
        if not urls:
            raise ValueError("No URLs to scrape")
        
        # Limit to first 50 for cost control in demo
        urls_to_scrape = urls[:50]
        print(f"Scraping {len(urls_to_scrape)} product pages...")
        
        hook = OlostepHook(olostep_conn_id="olostep_default")
        
        # Start batch job with completion waiting
        result = hook.batch_scrape(
            urls=urls_to_scrape,
            formats=["markdown", "text"],
        )
        
        batch_id = result.get("batch_id") or result.get("id")
        print(f"Batch job started: {batch_id}")
        
        # Wait for completion (with timeout)
        final_result = hook.wait_for_batch(
            batch_id=batch_id,
            poll_interval=15,
            timeout=3600,
        )
        
        return final_result
    
    scrape_products = PythonOperator(
        task_id="batch_scrape_products",
        python_callable=batch_scrape_products,
        doc_md="Batch scrape all discovered product pages.",
    )
    
    # Task 4: Extract pricing information using AI
    def extract_pricing_data(**context) -> List[Dict[str, Any]]:
        """Extract structured pricing data from scraped content."""
        ti = context["ti"]
        batch_results = ti.xcom_pull(task_ids="batch_scrape_products")
        
        if not batch_results:
            print("No batch results to process")
            return []
        
        results = batch_results.get("results", [])
        print(f"Processing {len(results)} scraped pages...")
        
        products = []
        hook = OlostepHook(olostep_conn_id="olostep_default")
        
        # Extract pricing from each product (using ask API for structured extraction)
        for i, result in enumerate(results[:10]):  # Limit for demo
            url = result.get("url", "")
            
            if not url:
                continue
            
            try:
                answer = hook.ask(
                    url=url,
                    question="Extract the product name, price, and availability as JSON.",
                )
                
                products.append({
                    "url": url,
                    "extracted_data": answer.get("answer", ""),
                    "scraped_at": datetime.utcnow().isoformat(),
                })
                
                print(f"Processed {i+1}/{min(len(results), 10)}: {url}")
                
            except Exception as e:
                print(f"Error processing {url}: {e}")
                continue
        
        print(f"Successfully extracted data from {len(products)} products")
        return products
    
    extract_pricing = PythonOperator(
        task_id="extract_pricing_data",
        python_callable=extract_pricing_data,
        doc_md="Extract structured pricing data using AI.",
    )
    
    # Task 5: Save results (placeholder - integrate with your data warehouse)
    def save_to_warehouse(**context):
        """Save extracted product data to data warehouse."""
        ti = context["ti"]
        products = ti.xcom_pull(task_ids="extract_pricing_data") or []
        
        print(f"Saving {len(products)} products to data warehouse...")
        
        # In production, you would:
        # - Save to PostgreSQL, BigQuery, Snowflake, etc.
        # - Update price history tables
        # - Trigger alerts for significant price changes
        
        for product in products:
            print(f"  - {product['url']}")
        
        return {
            "products_saved": len(products),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    save_results = PythonOperator(
        task_id="save_to_warehouse",
        python_callable=save_to_warehouse,
        doc_md="Save extracted data to data warehouse.",
    )
    
    end = EmptyOperator(
        task_id="end",
        trigger_rule="none_failed_min_one_success",
    )
    
    # Define pipeline flow
    start >> discover_products >> branch
    branch >> no_products >> end
    branch >> scrape_products >> extract_pricing >> save_results >> end
