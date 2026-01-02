APCloudy Documentation
=====================

Welcome to APCloudy's documentation! APCloudy is a Python client library for interacting with the APCloudy web scraping platform.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api_reference

Features
--------

* **Project Management**: Create, update, and manage your APCloudy projects
* **Spider Management**: Deploy and manage web scraping spiders
* **Job Management**: Start, monitor, and manage scraping jobs
* **Authentication**: Secure API key-based authentication
* **Error Handling**: Comprehensive error handling with custom exceptions

Getting Started
---------------

To get started with APCloudy, install it using pip:

.. code-block:: bash

   pip install apcloudy

Then initialize the client with your API key:

.. code-block:: python

   from apcloudy import APCloudyClient

   client = APCloudyClient("your-api-key-here")
   projects = client.get_projects()

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
