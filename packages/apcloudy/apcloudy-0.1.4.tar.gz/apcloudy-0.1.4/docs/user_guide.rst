
   # Stop all running jobs in a project
   running_jobs = client.get_jobs("project-123", state="running")
   for job in running_jobs:
       client.stop_job(job.id)

Data Retrieval
--------------

Downloading Scraped Data
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get job data as JSON
   data = client.get_job_data("job-456", format="json")

   # Save to file
   with open('scraped_data.json', 'w') as f:
       json.dump(data, f, indent=2)

   # Get data as CSV
   csv_data = client.get_job_data("job-456", format="csv")
   with open('scraped_data.csv', 'w') as f:
       f.write(csv_data)

Streaming Large Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Stream data for large jobs
   for batch in client.stream_job_data("job-456", batch_size=1000):
       # Process batch of items
       process_items(batch)

Data Filtering
~~~~~~~~~~~~~~

.. code-block:: python

   # Filter data by fields
   filtered_data = client.get_job_data(
       "job-456",
       fields=['title', 'price', 'url']
   )

   # Filter by date range
   recent_data = client.get_job_data(
       "job-456",
       start_date="2025-01-01",
       end_date="2025-01-31"
   )

Advanced Features
-----------------

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Start multiple jobs
   job_ids = client.start_batch_jobs(
       project_id="project-123",
       spider_name="product_spider",
       job_configs=[
           {'start_urls': ['https://site1.com']},
           {'start_urls': ['https://site2.com']},
           {'start_urls': ['https://site3.com']}
       ]
   )

Scheduling Jobs
~~~~~~~~~~~~~~~

.. code-block:: python

   # Schedule a job to run daily
   schedule = client.create_schedule(
       project_id="project-123",
       spider_name="product_spider",
       cron_expression="0 2 * * *",  # Run at 2 AM daily
       job_settings={'max_pages': 50}
   )

Webhooks
~~~~~~~~

.. code-block:: python

   # Set up webhook for job completion
   webhook = client.create_webhook(
       project_id="project-123",
       url="https://your-app.com/webhook",
       events=['job.completed', 'job.failed']
   )

Rate Limiting
~~~~~~~~~~~~~

APCloudy automatically handles rate limiting, but you can customize the behavior:

.. code-block:: python

   # Configure rate limiting
   client.configure_rate_limit(
       requests_per_minute=60,
       burst_size=10
   )

Best Practices
--------------

Performance Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

1. **Use appropriate delays**: Don't overwhelm target servers
2. **Limit concurrent requests**: Start with conservative settings
3. **Monitor resource usage**: Check CPU and memory consumption
4. **Use efficient selectors**: Optimize XPath and CSS selectors

Error Handling
~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy.exceptions import *

   def robust_scraping():
       try:
           job = client.start_job("project-123", "spider-name")
           return monitor_job_with_retry(job.id)
       except RateLimitError:
           print("Rate limited, waiting...")
           time.sleep(60)
           return robust_scraping()  # Retry
       except AuthenticationError:
           print("Authentication failed, check API key")
           raise
       except APIError as e:
           print(f"API error: {e}")
           raise

Resource Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Clean up old jobs
   old_jobs = client.get_jobs(
       "project-123",
       start_date="2025-01-01",
       end_date="2025-01-31"
   )

   for job in old_jobs:
       if job.state == JobState.COMPLETED:
           client.delete_job(job.id)

Debugging
~~~~~~~~~

.. code-block:: python

   # Enable debug logging
   import logging
   logging.basicConfig(level=logging.DEBUG)

   # Get detailed job logs
   logs = client.get_job_logs("job-456")
   for log_entry in logs:
       print(f"{log_entry.timestamp}: {log_entry.message}")

Data Quality
~~~~~~~~~~~~

.. code-block:: python

   # Validate scraped data
   def validate_job_data(job_id):
       data = client.get_job_data(job_id)

       # Check for required fields
       for item in data:
           if not item.get('title') or not item.get('price'):
               print(f"Warning: Incomplete item {item.get('url')}")

       return data
User Guide
==========

This comprehensive guide covers all aspects of using APCloudy for web scraping automation.

Authentication
--------------

API Key Management
~~~~~~~~~~~~~~~~~~

APCloudy uses API key authentication. You can provide your API key in several ways:

**Method 1: Direct initialization**

.. code-block:: python

   from apcloudy import APCloudyClient
   client = APCloudyClient("your-api-key-here")

**Method 2: Environment variable**

.. code-block:: bash

   export APCLOUDY_API_KEY="your-api-key-here"

.. code-block:: python

   client = APCloudyClient()  # Automatically uses environment variable

**Method 3: Configuration file**

Create a `.apcloudy` config file in your home directory:

.. code-block:: ini

   [default]
   api_key = your-api-key-here
   base_url = https://api.apcloudy.com

Security Best Practices
~~~~~~~~~~~~~~~~~~~~~~~

* Never commit API keys to version control
* Use environment variables in production
* Rotate API keys regularly
* Use different keys for development and production

Project Management
------------------

Projects are containers for your web scraping spiders and jobs.

Creating Projects
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create a new project
   project = client.create_project(
       name="E-commerce Scraper",
       description="Scraping product data from various e-commerce sites"
   )
   print(f"Created project: {project.id}")

Listing Projects
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get all projects
   projects = client.get_projects()

   # Display projects in a table
   for project in projects:
       print(f"ID: {project.id}, Name: {project.name}")

Updating Projects
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Update project details
   updated_project = client.update_project(
       project_id="project-123",
       name="Updated Project Name",
       description="New description"
   )

Deleting Projects
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Delete a project (this will also delete all spiders and jobs)
   client.delete_project("project-123")

Spider Management
-----------------

Spiders are the core components that define how to scrape websites.

Deploying Spiders
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Deploy a spider from a file
   with open('my_spider.py', 'r') as f:
       spider_code = f.read()

   spider = client.deploy_spider(
       project_id="project-123",
       spider_name="product_spider",
       spider_code=spider_code
   )

Listing Spiders
~~~~~~~~~~~~~~~

.. code-block:: python

   # Get all spiders in a project
   spiders = client.get_spiders("project-123")

   for spider in spiders:
       print(f"Spider: {spider.name}, Version: {spider.version}")

Spider Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get spider details including configuration
   spider = client.get_spider("project-123", "product_spider")

   # Update spider settings
   client.update_spider(
       project_id="project-123",
       spider_name="product_spider",
       settings={
           'DOWNLOAD_DELAY': 1,
           'CONCURRENT_REQUESTS': 16,
           'ROBOTSTXT_OBEY': True
       }
   )

Job Management
--------------

Jobs represent individual scraping runs of your spiders.

Starting Jobs
~~~~~~~~~~~~~

.. code-block:: python

   # Start a basic job
   job = client.start_job(
       project_id="project-123",
       spider_name="product_spider"
   )

   # Start a job with custom parameters
   job = client.start_job(
       project_id="project-123",
       spider_name="product_spider",
       job_settings={
           'start_urls': ['https://example.com/products'],
           'max_pages': 100
       }
   )

Monitoring Jobs
~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from apcloudy.models import JobState

   # Monitor job progress
   def monitor_job(job_id):
       while True:
           job = client.get_job(job_id)
           print(f"Job {job_id}: {job.state}")

           if job.state == JobState.COMPLETED:
               print(f"Job completed! Scraped {job.items_scraped} items")
               break
           elif job.state == JobState.FAILED:
               print(f"Job failed: {job.error_message}")
               break

           time.sleep(10)  # Check every 10 seconds

   # Start monitoring
   monitor_job(job.id)

Job Statistics
~~~~~~~~~~~~~~

.. code-block:: python

   # Get detailed job information
   job = client.get_job("job-456")

   print(f"Items scraped: {job.items_scraped}")
   print(f"Requests made: {job.requests_made}")
   print(f"Duration: {job.duration}")
   print(f"Start time: {job.start_time}")
   print(f"End time: {job.end_time}")

Stopping Jobs
~~~~~~~~~~~~~

.. code-block:: python

   # Stop a running job
   client.stop_job("job-456")
