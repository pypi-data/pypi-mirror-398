"""
Manages project operations in APCloudy.

This module includes the ProjectManager class to perform operations related to projects,
including retrieving project information and providing access to jobs and spiders managers.
"""

from typing import TYPE_CHECKING

from .models import Project
from .exceptions import APIError, ProjectNotFoundError
from .jobs_manager import JobsManager
from .spiders_manager import SpidersManager

if TYPE_CHECKING:
    from .client import APCloudyClient


class ProjectManager:
    """Manages a specific project"""

    def __init__(self, client: 'APCloudyClient', project_id: int):
        self.client = client
        self.project_id = project_id
        self.jobs = JobsManager(client, project_id)
        self.spiders = SpidersManager(client, project_id)

    def get_info(self) -> Project:
        """
        Get project information

        Returns:
            Project: Project details
        """
        try:
            response = self.client.http_request('GET', f'project/{self.project_id}')
            return Project.from_dict(response)
        except APIError as e:
            if e.status_code == 404:
                raise ProjectNotFoundError(f"Project {self.project_id} not found")
            raise
