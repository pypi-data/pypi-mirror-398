Error Handling
==============

APCloudy provides comprehensive error handling with specific exceptions for different error conditions. This guide covers how to handle errors gracefully in your applications.

Exception Hierarchy
-------------------

APCloudy exceptions follow a clear hierarchy:

.. code-block:: text

   APCloudyException (base exception)
   ├── APIError (general API errors)
   │   ├── AuthenticationError (401 errors)
   │   ├── ProjectNotFoundError (404 errors)
   │   ├── RateLimitError (429 errors)
   │   └── ServerError (5xx errors)
   ├── ConfigurationError (configuration issues)
   └── ValidationError (data validation errors)

Exception Types
---------------

APCloudyException
~~~~~~~~~~~~~~~~~

Base exception for all APCloudy-related errors.

.. code-block:: python

   from apcloudy.exceptions import APCloudyException

   try:
       # APCloudy operations
       pass
   except APCloudyException as e:
       print(f"APCloudy error: {e}")

APIError
~~~~~~~~

General API error for HTTP-related issues.

.. code-block:: python

   from apcloudy.exceptions import APIError

   try:
       client.get_projects()
   except APIError as e:
       print(f"API Error: {e.message}")
       print(f"Status Code: {e.status_code}")
       print(f"Response: {e.response}")

AuthenticationError
~~~~~~~~~~~~~~~~~~~

Raised when API key is invalid or authentication fails.

.. code-block:: python

   from apcloudy.exceptions import AuthenticationError

   try:
       client = APCloudyClient("invalid-api-key")
       projects = client.get_projects()
   except AuthenticationError:
       print("Invalid API key. Please check your credentials.")

ProjectNotFoundError
~~~~~~~~~~~~~~~~~~~~

Raised when a requested project doesn't exist.

.. code-block:: python

   from apcloudy.exceptions import ProjectNotFoundError

   try:
       project = client.get_project("non-existent-project")
   except ProjectNotFoundError:
       print("Project not found. Please check the project ID.")

RateLimitError
~~~~~~~~~~~~~~

Raised when API rate limits are exceeded.

.. code-block:: python

   from apcloudy.exceptions import RateLimitError
   import time

   try:
       job = client.start_job("project-id", "spider-name")
   except RateLimitError as e:
       print(f"Rate limited. Retry after: {e.retry_after} seconds")
       time.sleep(e.retry_after)
       # Retry the operation

Error Handling Patterns
-----------------------

Basic Error Handling
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from apcloudy import APCloudyClient
   from apcloudy.exceptions import (
       AuthenticationError,
       ProjectNotFoundError,
       RateLimitError,
       APIError
   )

   def safe_get_projects(client):
       try:
           return client.get_projects()
       except AuthenticationError:
           print("Authentication failed. Check your API key.")
           return None
       except RateLimitError as e:
           print(f"Rate limited. Wait {e.retry_after} seconds.")
           return None
       except APIError as e:
           print(f"API error: {e.message}")
           return None
       except Exception as e:
           print(f"Unexpected error: {e}")
           return None

Retry with Exponential Backoff
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   import random
   from apcloudy.exceptions import RateLimitError, APIError

   def retry_with_backoff(func, max_retries=3, base_delay=1):
       """Execute function with exponential backoff retry logic"""
       for attempt in range(max_retries):
           try:
               return func()
           except RateLimitError as e:
               if attempt == max_retries - 1:
                   raise

               # Use server-provided retry-after if available
               delay = e.retry_after if hasattr(e, 'retry_after') else base_delay * (2 ** attempt)
               jitter = random.uniform(0, 0.1 * delay)

               print(f"Rate limited. Retrying in {delay + jitter:.2f} seconds...")
               time.sleep(delay + jitter)

           except APIError as e:
               if attempt == max_retries - 1:
                   raise

               # Only retry on server errors (5xx)
               if e.status_code >= 500:
                   delay = base_delay * (2 ** attempt)
                   jitter = random.uniform(0, 0.1 * delay)

                   print(f"Server error. Retrying in {delay + jitter:.2f} seconds...")
                   time.sleep(delay + jitter)
               else:
                   raise  # Don't retry client errors (4xx)

   # Usage
   def start_job():
       return client.start_job("project-id", "spider-name")

   job = retry_with_backoff(start_job, max_retries=5)

Context Manager for Error Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from contextlib import contextmanager
   from apcloudy.exceptions import APCloudyException

   @contextmanager
   def handle_apcloudy_errors():
       """Context manager for graceful error handling"""
       try:
           yield
       except AuthenticationError:
           print("Authentication failed. Please check your API key.")
       except ProjectNotFoundError as e:
           print(f"Resource not found: {e}")
       except RateLimitError as e:
           print(f"Rate limited. Please wait {e.retry_after} seconds.")
       except APIError as e:
           print(f"API error ({e.status_code}): {e.message}")
       except APCloudyException as e:
           print(f"APCloudy error: {e}")
       except Exception as e:
           print(f"Unexpected error: {e}")

   # Usage
   with handle_apcloudy_errors():
       projects = client.get_projects()
       for project in projects:
           spiders = client.get_spiders(project.id)

Advanced Error Handling
-----------------------

Circuit Breaker Pattern
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import time
   from enum import Enum
   from apcloudy.exceptions import APIError

   class CircuitState(Enum):
       CLOSED = "closed"
       OPEN = "open"
       HALF_OPEN = "half_open"

   class CircuitBreaker:
       def __init__(self, failure_threshold=5, timeout=60):
           self.failure_threshold = failure_threshold
           self.timeout = timeout
           self.failure_count = 0
           self.last_failure_time = None
           self.state = CircuitState.CLOSED

       def call(self, func, *args, **kwargs):
           if self.state == CircuitState.OPEN:
               if time.time() - self.last_failure_time > self.timeout:
                   self.state = CircuitState.HALF_OPEN
               else:
                   raise Exception("Circuit breaker is OPEN")

           try:
               result = func(*args, **kwargs)
               self.on_success()
               return result
           except Exception as e:
               self.on_failure()
               raise

       def on_success(self):
           self.failure_count = 0
           self.state = CircuitState.CLOSED

       def on_failure(self):
           self.failure_count += 1
           self.last_failure_time = time.time()

           if self.failure_count >= self.failure_threshold:
               self.state = CircuitState.OPEN

   # Usage
   circuit_breaker = CircuitBreaker()

   def safe_api_call():
       return circuit_breaker.call(client.get_projects)

Logging and Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   import json
   from datetime import datetime
   from apcloudy.exceptions import APCloudyException

   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('apcloudy.log'),
           logging.StreamHandler()
       ]
   )

   logger = logging.getLogger('apcloudy_client')

   class ErrorMonitor:
       def __init__(self):
           self.error_counts = {}
           self.error_log = []

       def log_error(self, error, context=None):
           """Log error with context information"""
           error_type = type(error).__name__

           # Count errors by type
           self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

           # Create error record
           error_record = {
               'timestamp': datetime.now().isoformat(),
               'error_type': error_type,
               'error_message': str(error),
               'context': context or {}
           }

           # Add specific error information
           if isinstance(error, APIError):
               error_record.update({
                   'status_code': getattr(error, 'status_code', None),
                   'response': getattr(error, 'response', None)
               })

           self.error_log.append(error_record)

           # Log to file
           logger.error(f"APCloudy Error: {json.dumps(error_record)}")

           # Alert on critical errors
           if error_type in ['AuthenticationError', 'ServerError']:
               self.send_alert(error_record)

       def send_alert(self, error_record):
           """Send alert for critical errors"""
           # Implement your alerting mechanism (email, Slack, etc.)
           print(f"ALERT: Critical error - {error_record}")

       def get_error_summary(self):
           """Get summary of errors"""
           return {
               'total_errors': len(self.error_log),
               'error_counts': self.error_counts,
               'recent_errors': self.error_log[-10:]  # Last 10 errors
           }

   # Usage
   error_monitor = ErrorMonitor()

   def monitored_operation(operation, context=None):
       try:
           return operation()
       except APCloudyException as e:
           error_monitor.log_error(e, context)
           raise

Error Recovery Strategies
-------------------------

Graceful Degradation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def get_projects_with_fallback(client):
       """Get projects with fallback to cached data"""
       try:
           # Try to get fresh data
           projects = client.get_projects()

           # Cache successful response
           cache_projects(projects)
           return projects

       except APIError:
           # Fall back to cached data
           cached_projects = get_cached_projects()
           if cached_projects:
               print("Using cached project data due to API error")
               return cached_projects

           # Final fallback to empty list
           print("No cached data available, returning empty list")
           return []

   def cache_projects(projects):
       """Cache projects data"""
       # Implement your caching mechanism
       pass

   def get_cached_projects():
       """Retrieve cached projects"""
       # Implement your cache retrieval
       pass

Partial Success Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def bulk_operation_with_partial_success(operations):
       """Execute bulk operations, collecting both successes and failures"""
       successes = []
       failures = []

       for i, operation in enumerate(operations):
           try:
               result = operation()
               successes.append({
                   'index': i,
                   'result': result
               })
           except Exception as e:
               failures.append({
                   'index': i,
                   'error': str(e),
                   'error_type': type(e).__name__
               })

       return {
           'successes': successes,
           'failures': failures,
           'success_rate': len(successes) / len(operations) if operations else 0
       }

   # Usage
   operations = [
       lambda: client.start_job("project-1", "spider-1"),
       lambda: client.start_job("project-2", "spider-2"),
       lambda: client.start_job("project-3", "spider-3"),
   ]

   results = bulk_operation_with_partial_success(operations)
   print(f"Success rate: {results['success_rate']:.2%}")

Testing Error Conditions
-------------------------

Mock Error Responses
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import unittest
   from unittest.mock import patch, Mock
   from apcloudy import APCloudyClient
   from apcloudy.exceptions import RateLimitError, AuthenticationError

   class TestErrorHandling(unittest.TestCase):

       def setUp(self):
           self.client = APCloudyClient("test-api-key")

       @patch('apcloudy.client.requests.Session.get')
       def test_rate_limit_error(self, mock_get):
           # Mock rate limit response
           mock_response = Mock()
           mock_response.status_code = 429
           mock_response.headers = {'Retry-After': '60'}
           mock_response.json.return_value = {'error': 'Rate limit exceeded'}
           mock_get.return_value = mock_response

           with self.assertRaises(RateLimitError) as context:
               self.client.get_projects()

           self.assertEqual(context.exception.retry_after, 60)

       @patch('apcloudy.client.requests.Session.get')
       def test_authentication_error(self, mock_get):
           # Mock authentication error
           mock_response = Mock()
           mock_response.status_code = 401
           mock_response.json.return_value = {'error': 'Invalid API key'}
           mock_get.return_value = mock_response

           with self.assertRaises(AuthenticationError):
               self.client.get_projects()

Integration Testing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   def test_error_recovery_integration():
       """Integration test for error recovery"""
       client = APCloudyClient("test-api-key")

       # Test with invalid API key
       try:
           projects = client.get_projects()
           assert False, "Should have raised AuthenticationError"
       except AuthenticationError:
           print("✓ Authentication error handled correctly")

       # Test with valid API key but rate limiting
       client.api_key = "valid-api-key"

       # Simulate rapid requests to trigger rate limiting
       for i in range(200):  # Assuming rate limit is 100/minute
           try:
               client.get_projects()
           except RateLimitError:
               print("✓ Rate limiting detected and handled")
               break

Best Practices
--------------

1. **Always handle specific exceptions** rather than catching all exceptions
2. **Log errors with sufficient context** for debugging
3. **Implement retry logic** for transient errors
4. **Use circuit breakers** for external service calls
5. **Provide meaningful error messages** to users
6. **Monitor error rates** and set up alerts
7. **Test error conditions** in your test suite
8. **Document error handling** in your application
9. **Use graceful degradation** when possible
10. **Validate input data** before making API calls

Error Handling Checklist
------------------------

Before deploying your APCloudy integration:

- [ ] Handle all specific APCloudy exceptions
- [ ] Implement retry logic for transient errors
- [ ] Add logging for all error conditions
- [ ] Test error scenarios in your test suite
- [ ] Set up monitoring and alerting
- [ ] Document error handling for your team
- [ ] Implement graceful degradation where possible
- [ ] Validate configuration and input data
- [ ] Use appropriate timeouts
- [ ] Plan for rate limiting scenarios
