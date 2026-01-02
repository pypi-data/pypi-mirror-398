"""
Main client for interacting with the APCloudy API.

This module includes the APCloudyClient class which provides methods to make
authenticated HTTP requests and manage projects.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin

from .models import Project
from .config import config
from .exceptions import (
    APIError, AuthenticationError, ProjectNotFoundError, RateLimitError
)
from .project_manager import ProjectManager


class APCloudyClient:
    """
    Represents a client for interacting with the APCloudy API.

    This class provides methods to make authenticated HTTP requests, manage projects
    (e.g., retrieval, creation, and listing), and validate the connection with the APCloudy API.
    The client supports additional features such as retry logic for transient errors
    and rate-limiting compliance.

    :ivar api_key: The API key is used for authentication with the APCloudy API.
    :type api_key: Str
    :ivar base_url: The base URL for the APCloudy API.
    :type base_url: Str
    :ivar session: The session object used to handle HTTP requests.
    :type session: Requests.Session
    """

    def __init__(self, api_key: str = ''):
        """
        Initialize APCloudy client

        Args:
            api_key: Your APCloudy API key
        """
        # Set API key and validate configuration
        if api_key:
            config.api_key = api_key

        config.validate()

        self.api_key = config.api_key
        self.base_url = config.base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': f'apcloudy-client/0.1.0'
        })

        # Set request timeout from config
        self.session.timeout = config.request_timeout

    def http_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make API request with retry logic

        Args:
            method: HTTP method
            endpoint: API endpoint
            **kwargs: Additional arguments for requests

        Returns:
            Dict: API response data
        """

        url = urljoin(f"{self.base_url}/", endpoint)

        for attempt in range(config.max_retries + 1):
            try:
                response = self.session.request(method, url, **kwargs)
                status_code = response.status_code

                # Handle authentication errors
                if status_code == 401:
                    raise AuthenticationError("Invalid API key", status_code=401)

                # Handle other client/server errors
                if not response.ok:
                    message = response.json().get('error', f'Error Occured {status_code} {response.text}')
                    if status_code >= 500 and attempt < config.max_retries:
                        delay = config.retry_delay * (config.backoff_factor ** attempt)
                        time.sleep(delay)
                        continue
                    if status_code == 404:
                        raise Exception(message)

                    if status_code == 409:
                        raise APIError(message, status_code=status_code)

                    if status_code == 429:
                        raise RateLimitError(message, status_code=status_code)

                    if status_code == 400:
                        raise Exception(message)

                    raise APIError(message, status_code=status_code)

                return response.json()

            except requests.RequestException as e:
                if attempt < config.max_retries:
                    delay = config.retry_delay * (config.backoff_factor ** attempt)
                    time.sleep(delay)
                    continue
                raise APIError(f"Request failed: {str(e)}")

        # This should never be reached, but just in case
        raise APIError("Maximum retries exceeded")

    def get_project(self, project_id: int) -> ProjectManager:
        """
        Get a project manager for the specified project

        Args:
            project_id: Project ID

        Returns:
            ProjectManager: Project manager instance
        """
        return ProjectManager(self, project_id)

    def list_projects(self) -> Project:
        """
        List all projects

        Returns:
            List[Project]: Available projects
        """
        response = self.http_request('GET', 'projects/list')
        return Project.from_dict(response['projects'])

    def create_project(self, name: str, description: str = "") -> Project:
        """
        Create a new project

        Args:
            name: Project name
            description: Project description

        Returns:
            Project: Created project
        """
        data = {'name': name, 'description': description}
        response = self.http_request('POST', 'projects/create', json=data)
        return Project.from_dict(response)
