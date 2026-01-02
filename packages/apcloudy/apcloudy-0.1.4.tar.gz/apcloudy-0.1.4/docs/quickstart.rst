Quick Start Guide
=================

This guide will help you get started with APCloudy quickly.

Installation
------------

Install APCloudy using pip:

.. code-block:: bash

   pip install apcloudy

Basic Usage
-----------

Initialize the Client
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient

   # Initialize with your API key
   client = APCloudyClient("your-api-key-here")

   # Or set via environment variable
   import os
   os.environ['APCLOUDY_API_KEY'] = 'your-api-key-here'
   client = APCloudyClient()

Working with Projects
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List all projects
   projects = client.get_projects()
   print(f"Found {len(projects)} projects")

   # Get a specific project
   project = client.get_project("project-id")
   print(f"Project: {project.name}")

Working with Spiders
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # List spiders in a project
   spiders = client.get_spiders("project-id")

   # Get spider details
   spider = client.get_spider("project-id", "spider-name")
   print(f"Spider: {spider.name}")

Running Jobs
~~~~~~~~~~~~

.. code-block:: python

   # Start a scraping job
   job = client.start_job("project-id", "spider-name")
   print(f"Job started with ID: {job.id}")

   # Check job status
   job_status = client.get_job(job.id)
   print(f"Job state: {job_status.state}")

   # List all jobs for a project
   jobs = client.get_jobs("project-id")

Error Handling
--------------

.. code-block:: python

   from apcloudy import APCloudyClient
   from apcloudy.exceptions import (
       APIError,
       AuthenticationError,
       ProjectNotFoundError
   )

   client = APCloudyClient("your-api-key")

   try:
       projects = client.get_projects()
   except AuthenticationError:
       print("Invalid API key")
   except ProjectNotFoundError:
       print("Project not found")
   except APIError as e:
       print(f"API error: {e}")

Environment Variables
--------------------

You can configure APCloudy using environment variables:

.. code-block:: bash

   export APCLOUDY_API_KEY="your-api-key-here"
   export APCLOUDY_BASE_URL="https://api.apcloudy.com"  # optional

.. code-block:: python

   # Client will automatically use environment variables
   client = APCloudyClient()
