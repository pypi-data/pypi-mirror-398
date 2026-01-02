"""
Manages job operations for projects in APCloudy.

This module includes the JobsManager class to perform operations related to jobs
within specific projects. The operations include creating, retrieving, listing,
canceling, and deleting jobs, as well as retrieving logs and scraped items.
"""

import time
from typing import Dict, List, Optional, Any, Iterator, TYPE_CHECKING

from .models import Job, JobState
from .config import config
from .exceptions import APIError, JobNotFoundError

if TYPE_CHECKING:
    from .client import APCloudyClient


class JobsManager:
    """
    Manages job operations for a project in APCloudy, providing functionalities such as running,
    retrieving, listing, canceling, and deleting jobs, as well as retrieving logs or scraped items.
    It interacts with the APCloudyClient to perform HTTP requests for job-related actions.

    :ivar client: The client instance is used to communicate with the API.
    :type client: APCloudyClient
    :ivar project_id: The project ID for which jobs are managed.
    :type project_id: Int
    """

    def __init__(self, client: 'APCloudyClient', project_id: int):
        self.client = client
        self.project_id = project_id

    def run(self, spider_name: str,
            units: Optional[int] = None,
            job_args: Optional[Dict[str, Any]] = None,
            priority: Optional[int] = None,
            tags: Optional[List[str]] = None) -> List[Job]:
        """
        Run a spider job

        Args:
            spider_name: Name of the spider to run
            units: Number of units (parallel instances) to run
            job_args: Arguments to pass to the spider
            priority: Job priority (higher = higher priority)
            tags: Tags for job organization

        Returns:
            Job: The created job instance
        """
        # Validate configuration before using config values
        config.validate()
        data = {
            'job_id': config.current_job_id,
            'spider': spider_name,
            'project': self.project_id,
            'units': units or config.default_units,
            'job_args': job_args or {},
            'priority': priority or config.default_priority,
            'tags': tags or []
        }

        response = self.client.http_request('POST', 'job/run', json=data)
        return Job.from_dict([response['job']])

    def get(self, job_id: str) -> List[Job]:
        """
        Get job details

        Args:
            job_id: Job ID

        Returns:
            Job: Job instance with current status
        """
        try:
            response = self.client.http_request('GET', f'job/{self.project_id}', params={'job_id': job_id})
            return Job.from_dict(response['jobs'])
        except APIError as e:
            if e.status_code == 404:
                raise JobNotFoundError(f"Job {job_id} not found")
            raise

    def list(self, state: Optional[JobState] = None,
             spider: Optional[str] = None) -> list[Job]:
        """
        List jobs for the project

        Args:
            state: Filter by job state
            spider: Filter by spider name

        Returns:
            List[Job]: List of jobs
        """
        # Validate configuration before using config values
        config.validate()

        params = {}
        if state:
            if isinstance(state, JobState):
                params['status'] = state.value
        if spider:
            params['spider'] = spider

        response = self.client.http_request('GET', f'jobs/list/{self.project_id}', params=params)

        return Job.from_dict(response['jobs'])

    def cancel(self, job_id: str) -> bool:
        """
        Cancel a running job

        Args:
            job_id: Job ID to cancel

        Returns:
            bool: True if canceled successfully
        """
        body = {'action': 'Cancel', 'job_ids': [job_id]}
        try:
            response = self.client.http_request('POST', f'job/action', json=body)
            if response.get('success'):
                print(f"{job_id} Job canceled successfully")
                return True
            return False
        except APIError as e:
            if e.status_code == 404:
                raise JobNotFoundError(f"Job {job_id} not found")
            return False

    def delete(self, job_id: str) -> bool:
        """
        Delete a job and its data

        Args:
            job_id: Job ID to delete

        Returns:
            bool: True if deleted successfully
        """
        body = {'action': 'Delete', 'job_ids': [job_id]}
        try:
            response = self.client.http_request('POST', f'job/action', json=body)
            if response.get('success'):
                print(f"{job_id} Job deleted successfully")
                return True
            return False
        except APIError as e:
            if e.status_code == 404:
                raise JobNotFoundError(f"Job {job_id} not found")
            return False
