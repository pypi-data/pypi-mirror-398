"""
A module for interacting with the APCloudy platform.

This module provides functionalities to interact with the APCloudy platform,
including managing configurations, handling jobs and projects, and interacting
with spiders. It also provides utilities for handling HTTP requests and
responses, as well as error handling specific to the platform.

Exports:
- APCloudyClient: A client for making HTTP requests to the APCloudy API.
- config: Configuration handling for the module and application.
- Job: Represents a job in the APCloudy platform.
- JobState: Represents the state of a job in the APCloudy platform.
- Spider: Represents a spider in the APCloudy platform.
- Project: Represents a project in the APCloudy platform.
- Exceptions: APCloudy-specific exceptions for error handling.
- Utilities: Helper functions like `chunk_urls` for processing data.
"""

# Import main client and managers
from .client import APCloudyClient
from .jobs_manager import JobsManager
from .spiders_manager import SpidersManager
from .project_manager import ProjectManager

# Import models
from .models import Job, JobState, Spider, Project

# Import exceptions
from .exceptions import (
    APIError,
    AuthenticationError,
    JobNotFoundError,
    ProjectNotFoundError,
    SpiderNotFoundError,
    RateLimitError
)

# Import config
from .config import config

# Import utilities
from .utils import chunk_urls

__version__ = "0.1.4"

__all__ = [
    # Main client and managers
    'APCloudyClient',
    'JobsManager',
    'SpidersManager',
    'ProjectManager',

    # Models
    'Job',
    'JobState',
    'Spider',
    'Project',

    # Exceptions
    'APIError',
    'AuthenticationError',
    'JobNotFoundError',
    'ProjectNotFoundError',
    'SpiderNotFoundError',
    'RateLimitError',

    # Config
    'config',

    # Utilities
    'chunk_urls',
]
