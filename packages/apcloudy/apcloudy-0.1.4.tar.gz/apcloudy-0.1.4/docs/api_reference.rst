API Reference
=============

This section provides documentation for the main APCloudy classes and methods.

.. currentmodule:: apcloudy

APCloudyClient
--------------

.. autoclass:: APCloudyClient
   :members:
   :undoc-members:
   :show-inheritance:

Main Methods
~~~~~~~~~~~~

**Project Operations**

* ``get_projects()`` - List all projects
* ``get_project(project_id)`` - Get a specific project

**Spider Operations**

* ``get_spiders(project_id)`` - List spiders in a project
* ``get_spider(project_id, spider_name)`` - Get a specific spider

**Job Operations**

* ``get_jobs(project_id)`` - List jobs for a project
* ``get_job(job_id)`` - Get job details
* ``start_job(project_id, spider_name)`` - Start a new job
* ``stop_job(job_id)`` - Stop a running job

Models
------

Job State
~~~~~~~~~

.. autoclass:: apcloudy.models.JobState
   :members:
   :undoc-members:

Job
~~~

.. autoclass:: apcloudy.models.Job
   :members:
   :undoc-members:

Spider
~~~~~~

.. autoclass:: apcloudy.models.Spider
   :members:
   :undoc-members:

Project
~~~~~~~

.. autoclass:: apcloudy.models.Project
   :members:
   :undoc-members:

Exceptions
----------

.. automodule:: apcloudy.exceptions
   :members:
   :undoc-members:
