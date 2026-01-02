Examples
========

This section provides practical examples for common APCloudy use cases.

Basic Examples
--------------

Simple Web Scraping
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   import time

   # Initialize client
   client = APCloudyClient("your-api-key")

   # Create a project
   project = client.create_project(
       name="News Scraper",
       description="Scraping latest news articles"
   )

   # Spider code for scraping news
   spider_code = '''
   import scrapy

   class NewsSpider(scrapy.Spider):
       name = 'news'
       start_urls = ['https://example-news.com']

       def parse(self, response):
           for article in response.css('article.news-item'):
               yield {
                   'title': article.css('h2::text').get(),
                   'url': article.css('a::attr(href)').get(),
                   'summary': article.css('p.summary::text').get(),
                   'date': article.css('time::attr(datetime)').get(),
               }
   '''

   # Deploy spider
   spider = client.deploy_spider(
       project_id=project.id,
       spider_name="news",
       spider_code=spider_code
   )

   # Start scraping job
   job = client.start_job(project.id, "news")
   print(f"Job started: {job.id}")

   # Wait for completion
   while True:
       job_status = client.get_job(job.id)
       if job_status.state == "completed":
           break
       time.sleep(5)

   # Download results
   data = client.get_job_data(job.id)
   print(f"Scraped {len(data)} articles")

E-commerce Product Scraping
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   import json

   client = APCloudyClient("your-api-key")

   # Create e-commerce project
   project = client.create_project(
       name="Product Scraper",
       description="Scraping product information from e-commerce sites"
   )

   # Product spider with pagination
   spider_code = '''
   import scrapy

   class ProductSpider(scrapy.Spider):
       name = 'products'

       def start_requests(self):
           start_urls = getattr(self, 'start_urls', ['https://example-shop.com/products'])
           for url in start_urls:
               yield scrapy.Request(url, self.parse)

       def parse(self, response):
           # Extract product links
           product_links = response.css('a.product-link::attr(href)').getall()

           for link in product_links:
               yield response.follow(link, self.parse_product)

           # Follow pagination
           next_page = response.css('a.next-page::attr(href)').get()
           if next_page:
               yield response.follow(next_page, self.parse)

       def parse_product(self, response):
           yield {
               'name': response.css('h1.product-title::text').get(),
               'price': response.css('.price::text').re_first(r'[\d.]+'),
               'description': response.css('.description::text').get(),
               'in_stock': response.css('.stock-status::text').get(),
               'rating': response.css('.rating::attr(data-rating)').get(),
               'reviews_count': response.css('.reviews-count::text').re_first(r'\d+'),
               'url': response.url,
               'image_urls': response.css('.product-images img::attr(src)').getall(),
           }
   '''

   # Deploy with custom settings
   spider = client.deploy_spider(
       project_id=project.id,
       spider_name="products",
       spider_code=spider_code
   )

   # Configure spider settings for respectful scraping
   client.update_spider(
       project_id=project.id,
       spider_name="products",
       settings={
           'DOWNLOAD_DELAY': 2,
           'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
           'CONCURRENT_REQUESTS': 8,
           'ROBOTSTXT_OBEY': True,
           'USER_AGENT': 'ProductBot 1.0'
       }
   )

   # Start job with custom parameters
   job = client.start_job(
       project_id=project.id,
       spider_name="products",
       job_settings={
           'start_urls': ['https://example-shop.com/electronics'],
           'max_pages': 50
       }
   )

Advanced Examples
-----------------

Multi-site Data Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   from concurrent.futures import ThreadPoolExecutor
   import time

   client = APCloudyClient("your-api-key")

   # Websites to scrape
   websites = [
       {'name': 'site1', 'url': 'https://example1.com'},
       {'name': 'site2', 'url': 'https://example2.com'},
       {'name': 'site3', 'url': 'https://example3.com'},
   ]

   def scrape_website(website):
       """Scrape a single website"""
       project_name = f"Scraper-{website['name']}"

       # Create project for this website
       project = client.create_project(
           name=project_name,
           description=f"Scraping {website['name']}"
       )

       # Deploy universal spider
       universal_spider_code = '''
       import scrapy

       class UniversalSpider(scrapy.Spider):
           name = 'universal'

           def parse(self, response):
               # Extract all links
               links = response.css('a::attr(href)').getall()

               # Extract text content
               text_content = response.css('p::text, h1::text, h2::text, h3::text').getall()

               yield {
                   'url': response.url,
                   'title': response.css('title::text').get(),
                   'links': links[:10],  # First 10 links
                   'content': ' '.join(text_content)[:500],  # First 500 chars
                   'scraped_at': response.meta.get('download_latency')
               }
       '''

       spider = client.deploy_spider(
           project_id=project.id,
           spider_name="universal",
           spider_code=universal_spider_code
       )

       # Start job
       job = client.start_job(
           project_id=project.id,
           spider_name="universal",
           job_settings={'start_urls': [website['url']]}
       )

       return {
           'website': website['name'],
           'project_id': project.id,
           'job_id': job.id
       }

   # Run scraping jobs in parallel
   with ThreadPoolExecutor(max_workers=3) as executor:
       futures = [executor.submit(scrape_website, site) for site in websites]
       jobs = [future.result() for future in futures]

   # Monitor all jobs
   def monitor_all_jobs(jobs):
       completed = set()

       while len(completed) < len(jobs):
           for job_info in jobs:
               if job_info['job_id'] not in completed:
                   job = client.get_job(job_info['job_id'])
                   print(f"{job_info['website']}: {job.state}")

                   if job.state in ['completed', 'failed']:
                       completed.add(job_info['job_id'])

           if len(completed) < len(jobs):
               time.sleep(10)

       print("All jobs completed!")

   monitor_all_jobs(jobs)

Scheduled Data Collection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   import schedule
   import time

   client = APCloudyClient("your-api-key")

   def daily_news_scrape():
       """Run daily news scraping"""
       try:
           job = client.start_job(
               project_id="news-project-id",
               spider_name="news",
               job_settings={
                   'start_urls': ['https://news-site.com/latest'],
                   'max_pages': 20
               }
           )

           print(f"Daily news scrape started: {job.id}")

           # Send notification (webhook, email, etc.)
           send_notification(f"News scraping job {job.id} started")

       except Exception as e:
           print(f"Failed to start daily scrape: {e}")
           send_error_notification(str(e))

   def send_notification(message):
       """Send notification via webhook or email"""
       # Implementation depends on your notification system
       pass

   def send_error_notification(error):
       """Send error notification"""
       # Implementation for error alerts
       pass

   # Schedule daily scraping at 6 AM
   schedule.every().day.at("06:00").do(daily_news_scrape)

   # Keep the scheduler running
   while True:
       schedule.run_pending()
       time.sleep(60)

Data Processing Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   import pandas as pd
   import sqlite3
   from datetime import datetime

   client = APCloudyClient("your-api-key")

   class DataPipeline:
       def __init__(self, database_path="scraped_data.db"):
           self.client = client
           self.db_path = database_path
           self.setup_database()

       def setup_database(self):
           """Create database tables"""
           conn = sqlite3.connect(self.db_path)
           cursor = conn.cursor()

           cursor.execute('''
               CREATE TABLE IF NOT EXISTS products (
                   id INTEGER PRIMARY KEY,
                   name TEXT,
                   price REAL,
                   url TEXT UNIQUE,
                   scraped_at TIMESTAMP,
                   job_id TEXT
               )
           ''')

           conn.commit()
           conn.close()

       def process_job_data(self, job_id):
           """Process and store job data"""
           try:
               # Get raw data
               raw_data = self.client.get_job_data(job_id)

               # Clean and validate data
               cleaned_data = self.clean_data(raw_data)

               # Store in database
               self.store_data(cleaned_data, job_id)

               # Generate report
               report = self.generate_report(cleaned_data)

               return report

           except Exception as e:
               print(f"Error processing job {job_id}: {e}")
               return None

       def clean_data(self, raw_data):
           """Clean and validate scraped data"""
           df = pd.DataFrame(raw_data)

           # Remove duplicates
           df = df.drop_duplicates(subset=['url'])

           # Clean price data
           if 'price' in df.columns:
               df['price'] = pd.to_numeric(df['price'], errors='coerce')
               df = df.dropna(subset=['price'])

           # Validate required fields
           required_fields = ['name', 'url']
           df = df.dropna(subset=required_fields)

           return df.to_dict('records')

       def store_data(self, data, job_id):
           """Store cleaned data in database"""
           conn = sqlite3.connect(self.db_path)

           for item in data:
               try:
                   conn.execute('''
                       INSERT OR REPLACE INTO products
                       (name, price, url, scraped_at, job_id)
                       VALUES (?, ?, ?, ?, ?)
                   ''', (
                       item.get('name'),
                       item.get('price'),
                       item.get('url'),
                       datetime.now(),
                       job_id
                   ))
               except sqlite3.Error as e:
                   print(f"Database error: {e}")

           conn.commit()
           conn.close()

       def generate_report(self, data):
           """Generate summary report"""
           df = pd.DataFrame(data)

           report = {
               'total_items': len(df),
               'average_price': df['price'].mean() if 'price' in df.columns else None,
               'price_range': {
                   'min': df['price'].min() if 'price' in df.columns else None,
                   'max': df['price'].max() if 'price' in df.columns else None
               },
               'processed_at': datetime.now().isoformat()
           }

           return report

   # Usage
   pipeline = DataPipeline()

   # Process completed jobs
   completed_jobs = client.get_jobs("project-id", state="completed")

   for job in completed_jobs[-5:]:  # Process last 5 jobs
       report = pipeline.process_job_data(job.id)
       if report:
           print(f"Job {job.id}: {report['total_items']} items processed")

Error Recovery and Retry Logic
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   from apcloudy.exceptions import RateLimitError, APIError
   import time
   import random

   class RobustScraper:
       def __init__(self, api_key, max_retries=3):
           self.client = APCloudyClient(api_key)
           self.max_retries = max_retries

       def start_job_with_retry(self, project_id, spider_name, **kwargs):
           """Start job with exponential backoff retry"""
           for attempt in range(self.max_retries):
               try:
                   job = self.client.start_job(project_id, spider_name, **kwargs)
                   return job

               except RateLimitError:
                   if attempt < self.max_retries - 1:
                       wait_time = (2 ** attempt) + random.uniform(0, 1)
                       print(f"Rate limited, waiting {wait_time:.2f} seconds...")
                       time.sleep(wait_time)
                       continue
                   raise

               except APIError as e:
                   if attempt < self.max_retries - 1 and e.status_code >= 500:
                       wait_time = (2 ** attempt) + random.uniform(0, 1)
                       print(f"Server error, retrying in {wait_time:.2f} seconds...")
                       time.sleep(wait_time)
                       continue
                   raise

           raise Exception(f"Failed after {self.max_retries} attempts")

       def monitor_job_with_recovery(self, job_id):
           """Monitor job with automatic recovery"""
           consecutive_failures = 0
           max_failures = 5

           while True:
               try:
                   job = self.client.get_job(job_id)
                   consecutive_failures = 0  # Reset failure count

                   print(f"Job {job_id}: {job.state}")

                   if job.state in ['completed', 'failed']:
                       return job

                   time.sleep(10)

               except Exception as e:
                   consecutive_failures += 1
                   print(f"Error checking job status: {e}")

                   if consecutive_failures >= max_failures:
                       raise Exception(f"Too many consecutive failures: {e}")

                   # Exponential backoff
                   wait_time = min(300, 10 * (2 ** consecutive_failures))
                   time.sleep(wait_time)

   # Usage
   scraper = RobustScraper("your-api-key")

   try:
       job = scraper.start_job_with_retry("project-id", "spider-name")
       final_job = scraper.monitor_job_with_recovery(job.id)
       print(f"Job completed: {final_job.state}")
   except Exception as e:
       print(f"Scraping failed: {e}")

Integration Examples
--------------------

Django Integration
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # models.py
   from django.db import models
   from apcloudy import APCloudyClient

   class ScrapingJob(models.Model):
       job_id = models.CharField(max_length=100, unique=True)
       project_id = models.CharField(max_length=100)
       spider_name = models.CharField(max_length=100)
       status = models.CharField(max_length=50)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       def update_status(self):
           client = APCloudyClient()
           job = client.get_job(self.job_id)
           self.status = job.state
           self.save()

   # views.py
   from django.http import JsonResponse
   from django.views.decorators.http import require_POST
   from .models import ScrapingJob

   @require_POST
   def start_scraping(request):
       client = APCloudyClient()

       job = client.start_job(
           project_id=request.POST['project_id'],
           spider_name=request.POST['spider_name']
       )

       # Save to database
       scraping_job = ScrapingJob.objects.create(
           job_id=job.id,
           project_id=request.POST['project_id'],
           spider_name=request.POST['spider_name'],
           status=job.state
       )

       return JsonResponse({
           'job_id': job.id,
           'status': job.state
       })

Flask API Integration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from flask import Flask, request, jsonify
   from apcloudy import APCloudyClient
   import os

   app = Flask(__name__)
   client = APCloudyClient(os.environ.get('APCLOUDY_API_KEY'))

   @app.route('/api/projects', methods=['GET'])
   def get_projects():
       try:
           projects = client.get_projects()
           return jsonify([{
               'id': p.id,
               'name': p.name,
               'description': p.description
           } for p in projects])
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   @app.route('/api/jobs', methods=['POST'])
   def start_job():
       try:
           data = request.get_json()
           job = client.start_job(
               project_id=data['project_id'],
               spider_name=data['spider_name'],
               job_settings=data.get('settings', {})
           )

           return jsonify({
               'job_id': job.id,
               'status': job.state
           })
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   @app.route('/api/jobs/<job_id>/data', methods=['GET'])
   def get_job_data(job_id):
       try:
           data = client.get_job_data(job_id)
           return jsonify(data)
       except Exception as e:
           return jsonify({'error': str(e)}), 500

   if __name__ == '__main__':
       app.run(debug=True)
