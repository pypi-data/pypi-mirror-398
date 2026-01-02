Configuration
=============

APCloudy provides flexible configuration options to customize the client behavior for different environments and use cases.

Configuration Methods
---------------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

The recommended way to configure APCloudy in production:

.. code-block:: bash

   # Required
   export APCLOUDY_API_KEY="your-api-key-here"

   # Optional
   export APCLOUDY_BASE_URL="https://api.apcloudy.com"
   export APCLOUDY_TIMEOUT="30"
   export APCLOUDY_MAX_RETRIES="3"
   export APCLOUDY_RATE_LIMIT="100"

Configuration File
~~~~~~~~~~~~~~~~~~

Create a configuration file in your home directory or project root:

**~/.apcloudy/config.ini**

.. code-block:: ini

   [default]
   api_key = your-api-key-here
   base_url = https://api.apcloudy.com
   timeout = 30
   max_retries = 3
   rate_limit = 100

   [development]
   api_key = dev-api-key
   base_url = https://dev-api.apcloudy.com
   timeout = 60

   [production]
   api_key = prod-api-key
   base_url = https://api.apcloudy.com
   timeout = 30
   rate_limit = 50

**Using configuration profiles:**

.. code-block:: python

   from apcloudy import APCloudyClient
   from apcloudy.config import config

   # Load specific profile
   config.load_profile('development')
   client = APCloudyClient()

Programmatic Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure the client directly in your code:

.. code-block:: python

   from apcloudy import APCloudyClient
   from apcloudy.config import config

   # Configure globally
   config.api_key = "your-api-key"
   config.base_url = "https://api.apcloudy.com"
   config.timeout = 30
   config.max_retries = 3

   # Or configure per client
   client = APCloudyClient(
       api_key="your-api-key",
       base_url="https://api.apcloudy.com",
       timeout=30
   )

Configuration Options
--------------------

Authentication
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Option
     - Type
     - Description
   * - ``api_key``
     - string
     - Your APCloudy API key (required)
   * - ``auth_header``
     - string
     - Custom authentication header name (default: "Authorization")

Connection Settings
~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Option
     - Type
     - Description
   * - ``base_url``
     - string
     - APCloudy API base URL (default: "https://api.apcloudy.com")
   * - ``timeout``
     - integer
     - Request timeout in seconds (default: 30)
   * - ``verify_ssl``
     - boolean
     - Verify SSL certificates (default: True)
   * - ``proxies``
     - dict
     - HTTP proxies configuration

Retry and Rate Limiting
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Option
     - Type
     - Description
   * - ``max_retries``
     - integer
     - Maximum retry attempts (default: 3)
   * - ``retry_delay``
     - float
     - Initial retry delay in seconds (default: 1.0)
   * - ``retry_backoff``
     - float
     - Exponential backoff multiplier (default: 2.0)
   * - ``rate_limit``
     - integer
     - Requests per minute limit (default: 100)
   * - ``rate_limit_window``
     - integer
     - Rate limit window in seconds (default: 60)

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Option
     - Type
     - Description
   * - ``log_level``
     - string
     - Logging level ("DEBUG", "INFO", "WARNING", "ERROR")
   * - ``log_format``
     - string
     - Custom log format string
   * - ``log_file``
     - string
     - Path to log file (optional)

Advanced Configuration
----------------------

Custom HTTP Session
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import requests
   from apcloudy import APCloudyClient

   # Create custom session with specific settings
   session = requests.Session()
   session.headers.update({
       'User-Agent': 'MyApp/1.0 APCloudy Client'
   })

   # Configure proxy
   session.proxies = {
       'http': 'http://proxy.company.com:8080',
       'https': 'https://proxy.company.com:8080'
   }

   # Use custom session
   client = APCloudyClient(session=session)

SSL Configuration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient

   # Disable SSL verification (not recommended for production)
   client = APCloudyClient(verify_ssl=False)

   # Use custom CA certificate
   client = APCloudyClient(ca_cert_path="/path/to/ca-cert.pem")

   # Use client certificates
   client = APCloudyClient(
       client_cert="/path/to/client.crt",
       client_key="/path/to/client.key"
   )

Connection Pooling
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   from requests.adapters import HTTPAdapter
   from urllib3.util.retry import Retry

   # Configure connection pooling
   client = APCloudyClient()

   # Custom retry strategy
   retry_strategy = Retry(
       total=5,
       backoff_factor=1,
       status_forcelist=[429, 500, 502, 503, 504],
   )

   adapter = HTTPAdapter(
       pool_connections=10,
       pool_maxsize=20,
       max_retries=retry_strategy
   )

   client.session.mount("http://", adapter)
   client.session.mount("https://", adapter)

Environment-Specific Configurations
-----------------------------------

Development Environment
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config/development.py
   from apcloudy.config import config

   config.update({
       'api_key': 'dev-api-key',
       'base_url': 'https://dev-api.apcloudy.com',
       'timeout': 60,
       'log_level': 'DEBUG',
       'verify_ssl': False,  # For local development only
       'rate_limit': 1000,   # Higher rate limit for testing
   })

Production Environment
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config/production.py
   import os
   from apcloudy.config import config

   config.update({
       'api_key': os.environ['APCLOUDY_API_KEY'],
       'base_url': 'https://api.apcloudy.com',
       'timeout': 30,
       'log_level': 'INFO',
       'verify_ssl': True,
       'rate_limit': 50,     # Conservative rate limit
       'max_retries': 5,     # More retries for production
   })

Testing Environment
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config/testing.py
   from apcloudy.config import config

   config.update({
       'api_key': 'test-api-key',
       'base_url': 'https://test-api.apcloudy.com',
       'timeout': 10,
       'log_level': 'WARNING',
       'max_retries': 1,     # Fast failure for tests
       'rate_limit': None,   # No rate limiting in tests
   })

Configuration Validation
------------------------

APCloudy automatically validates configuration settings:

.. code-block:: python

   from apcloudy.config import config, ConfigurationError

   try:
       config.validate()
   except ConfigurationError as e:
       print(f"Configuration error: {e}")

Custom validation:

.. code-block:: python

   from apcloudy.config import config

   def validate_custom_config():
       """Custom configuration validation"""
       if not config.api_key:
           raise ValueError("API key is required")

       if config.timeout < 10:
           print("Warning: Timeout is very low")

       if config.rate_limit and config.rate_limit > 1000:
           print("Warning: Rate limit is very high")

   validate_custom_config()

Configuration Examples
----------------------

Multi-Environment Setup
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # config.py
   import os
   from apcloudy import APCloudyClient
   from apcloudy.config import config

   def get_client():
       env = os.environ.get('ENVIRONMENT', 'development')

       if env == 'production':
           config.load_profile('production')
       elif env == 'staging':
           config.load_profile('staging')
       else:
           config.load_profile('development')

       return APCloudyClient()

   # Usage
   client = get_client()

Docker Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: dockerfile

   # Dockerfile
   FROM python:3.9

   # Install APCloudy
   RUN pip install apcloudy

   # Set environment variables
   ENV APCLOUDY_API_KEY=""
   ENV APCLOUDY_BASE_URL="https://api.apcloudy.com"
   ENV APCLOUDY_TIMEOUT="30"
   ENV APCLOUDY_LOG_LEVEL="INFO"

   COPY . /app
   WORKDIR /app

   CMD ["python", "scraper.py"]

.. code-block:: yaml

   # docker-compose.yml
   version: '3.8'
   services:
     scraper:
       build: .
       environment:
         - APCLOUDY_API_KEY=${APCLOUDY_API_KEY}
         - APCLOUDY_BASE_URL=https://api.apcloudy.com
         - APCLOUDY_LOG_LEVEL=INFO
       volumes:
         - ./data:/app/data

Kubernetes Configuration
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   # configmap.yaml
   apiVersion: v1
   kind: ConfigMap
   metadata:
     name: apcloudy-config
   data:
     APCLOUDY_BASE_URL: "https://api.apcloudy.com"
     APCLOUDY_TIMEOUT: "30"
     APCLOUDY_LOG_LEVEL: "INFO"

   ---
   # secret.yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: apcloudy-secret
   type: Opaque
   data:
     APCLOUDY_API_KEY: <base64-encoded-api-key>

   ---
   # deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: scraper
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: scraper
     template:
       metadata:
         labels:
           app: scraper
       spec:
         containers:
         - name: scraper
           image: my-scraper:latest
           envFrom:
           - configMapRef:
               name: apcloudy-config
           - secretRef:
               name: apcloudy-secret

Troubleshooting Configuration
-----------------------------

Common Issues
~~~~~~~~~~~~~

**API Key not found:**

.. code-block:: python

   from apcloudy.config import config

   # Check if API key is set
   if not config.api_key:
       print("API key not configured")
       print("Set APCLOUDY_API_KEY environment variable")

**Connection issues:**

.. code-block:: python

   # Test connection
   try:
       client = APCloudyClient()
       projects = client.get_projects()
       print("Connection successful")
   except Exception as e:
       print(f"Connection failed: {e}")

**Rate limiting:**

.. code-block:: python

   from apcloudy.exceptions import RateLimitError

   try:
       # Your API calls
       pass
   except RateLimitError:
       print("Rate limit exceeded")
       print("Consider reducing rate_limit in configuration")

Debug Configuration
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy.config import config
   import logging

   # Enable debug logging
   logging.basicConfig(level=logging.DEBUG)

   # Print current configuration
   print("Current configuration:")
   for key, value in config.__dict__.items():
       if 'key' in key.lower():
           print(f"{key}: {'*' * len(str(value))}")  # Hide sensitive values
       else:
           print(f"{key}: {value}")

Configuration Best Practices
----------------------------

1. **Use environment variables** for sensitive data like API keys
2. **Version your configuration** files with your application code
3. **Validate configuration** before starting your application
4. **Use different configurations** for different environments
5. **Monitor configuration changes** in production
6. **Document configuration options** for your team
7. **Use secure methods** to distribute API keys
