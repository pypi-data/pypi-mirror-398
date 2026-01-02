"""
Manages spider operations for projects in APCloudy.

This module includes the SpidersManager class to perform operations related to spiders
within specific projects. The operations include listing and retrieving spider details.
"""

from typing import List, TYPE_CHECKING

from .models import Spider
from .exceptions import APIError, SpiderNotFoundError

if TYPE_CHECKING:
    from .client import APCloudyClient


class SpidersManager:
    """
    Manages spider operations within a specific project.

    This class provides the functionality to list, retrieve
    spiders associated with a project. It serves as an interface for working
    with spiders in the context of an APCloudyClient instance.

    :ivar client: The client used to interact with the spider API.
    :type client: APCloudyClient
    :ivar project_id: The ID of the project the spiders are associated with.
    :type project_id: int
    """

    def __init__(self, client: 'APCloudyClient', project_id: int):
        self.client = client
        self.project_id = project_id

    def list(self) -> List[Spider]:
        """
        List all spiders in the project

        Returns:
            List[Spider]: Available spiders
        """
        response = self.client.http_request('GET', f'spiders/list/{self.project_id}')
        return Spider.from_dict(response['spiders'])

    def get(self, spider_name: str) -> List[Spider]:
        """
        Get spider details

        Args:
            spider_name: Name of the spider

        Returns:
            Spider: Spider details
        """
        try:
            response = self.client.http_request('GET', f'spider/{self.project_id}/{spider_name}')
            return Spider.from_dict([response])
        except APIError as e:
            if e.status_code == 404:
                raise SpiderNotFoundError(f"Spider {spider_name} not found")
            raise
