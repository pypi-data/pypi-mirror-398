"""
This module defines classes and functionalities to handle scraping jobs,
spiders, and projects. It includes data representations for job execution
states, jobs, spiders, and projects.

The module provides detailed representations and helper methods to create
instances of these classes from dictionaries, typically corresponding to API
responses. It also includes properties and static methods to parse and format
relevant data.

Classes:
  - JobState: Enum for job execution states.
  - Job: Represents a scraping job, its attributes, and utility methods.
  - Spider: Represents a spider and its configurations.
  - Project: Represents a project and associated metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from tabulate import tabulate

from .config import config


class JobState(Enum):
    """
    Represents the state of a job in a task or workflow management system.

    This enumeration is used to define and manage the state of a job. It supports
    several states a job may transition through during its lifecycle, which can
    facilitate job tracking, control, and monitoring in various systems. Typical
    states include when a job is scheduled, actively running, completed, or
    deleted.
    """
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    DELETED = "deleted"


@dataclass
class Job:
    """
    Represents a job execution and maintains information related to job lifecycle,
    metrics, and associated resources.

    This class is used for tracking the progress, state, and details of a specific
    job. It can manage metadata such as creation time, start time, finish time, and
    other attributes that describe the job's execution process.

    :ivar job_id: Unique identifier for the job assigned by the system.
    :type job_id: str
    :ivar spider_name: Name of the spider used to execute the job.
    :type spider_name: str
    :ivar state: Current state of the job, represented as a JobState instance.
    :type state: JobState
    :ivar project_id: Identifier of the project the job belongs to.
    :type project_id: str
    :ivar created_at: Timestamp when the job was created, or None if not available.
    :type created_at: Optional[datetime]
    :ivar started_at: Timestamp when the job was started, or None if not available.
    :type started_at: Optional[datetime]
    :ivar finished_at: Timestamp when the job was finished, or None if not available.
    :type finished_at: Optional[datetime]
    :ivar items_scraped: Total number of items successfully scraped by the job.
    :type items_scraped: int
    :ivar requests_made: Total number of requests made during the job execution.
    :type requests_made: int
    :ivar job_args: Dictionary of additional arguments or configuration parameters
        passed to the job.
    :type job_args: Dict[str, Any]
    :ivar units: Number of resource units used (e.g., processing capacity) by
        the job.
    :type units: int
    :ivar logs_url: URL containing logs associated with the job, or None if not set.
    :type logs_url: Optional[str]
    :ivar items_url: URL containing scraped items for the job, or None if not set.
    :type items_url: Optional[str]
    """
    job_id: str
    spider_name: str
    state: JobState
    project_id: str = ""
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    items_scraped: int = 0
    requests_made: int = 0
    job_args: Dict[str, Any] = field(default_factory=dict)
    units: int = 1
    logs_url: Optional[str] = None
    items_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> List['Job']:
        """
        Creates a Job instance from a dictionary representation and displays the job details
        in a tabulated format.

        This method is primarily responsible for deserializing structured data into a Job
        instance and setting attributes accordingly. Additionally, it formats and prints
        job details like job ID, spider name, state, and timestamps in an organized layout.

        :param data: Dictionary containing the job data.
        :type data: Dict[str, Any]
        :return: A Job instance populated from the given data.
        :rtype: Job
        """
        jobs = []
        row_data = []
        for d in data:
            job = cls(
                job_id=d['job_id'],
                spider_name=d['spider_name'],
                state=JobState(d['status']),
                project_id=d.get('project_id', ''),
                created_at=cls._parse_datetime(d.get('created_at')),
                started_at=cls._parse_datetime(d.get('started_at')),
                finished_at=cls._parse_datetime(d.get('finished_at')),
                items_scraped=d.get('items_scraped', 0),
                requests_made=d.get('requests_made', 0),
                job_args=d.get('job_args', {}),
                units=d.get('units', 1),
                logs_url=d.get('logs_url'),
                items_url=d.get('items_url'),
            )

            jobs.append(job)

            config.current_job_id = d['job_id']

            row_data.append([
                job.job_id,
                job.spider_name,
                job.state.value,
                job.project_id or "N/A",
                job.created_at.strftime("%Y-%m-%d %H:%M:%S") if job.created_at else "N/A",
                job.started_at.strftime("%Y-%m-%d %H:%M:%S") if job.started_at else "N/A",
                job.finished_at.strftime("%Y-%m-%d %H:%M:%S") if job.finished_at else "N/A",
                job.items_scraped,
                job.requests_made,
                job.units,
                f"{job.duration:.2f}s" if job.duration else "N/A",
            ])

        # Display job data in table format with columns
        headers = ["Job ID", "Spider Name", "State", "Project ID", "Created At", "Started At", "Finished At", "Items", "Requests", "Units", "Duration"]

        print(tabulate(row_data, headers=headers, tablefmt="grid"))
        return jobs

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parses an ISO 8601 formatted date-time string into a ``datetime`` object.

        This static method attempts to parse the given date-time string. It handles
        ISO 8601 formats and ensures compatibility with UTC by replacing any 'Z'
        suffix in the string with '+00:00'. If the string is invalid or cannot be
        processed, the method returns ``None``.

        :param dt_str: The date-time string to be parsed. If provided, it must follow
            the ISO 8601 format. If ``None`` or empty, the method returns ``None``.
        :type dt_str: Optional[str]
        :return: A ``datetime`` object representing the parsed date-time, or ``None``
            if the input is invalid, empty, or cannot be processed.
        :rtype: Optional[datetime]
        """
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None

    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


@dataclass
class Spider:
    """Represents a spider"""
    name: str
    description: str = ""
    project_id: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: List[Dict[str, Any]]) -> List['Spider']:
        """Create Spider instance from API response"""
        spider: List[Spider] = []
        row_data = []

        # Display spider data in table format with columns
        headers = ["S.No", "Name", "Description", "Project ID"]
        for idx, sp in enumerate(data, start=1):
            row_data.append([idx,
                             sp.get('name'),
                             sp.get('description'),
                             sp.get('project_id'), ])
            spider.append(cls(
                name=sp['name'],
                description=sp.get('description', ''),
                project_id=sp.get('project_id', ''),
            ))

        print("SPIDER DETAILS")
        print(tabulate(row_data, headers=headers, tablefmt="grid"))
        return spider


@dataclass
class Project:
    """Represents a project"""
    project_id: str
    org_name: str
    name: str
    description: str = ""
    created_at: Optional[datetime] = None
    spider_count: int = 0
    job_count: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Project':
        """Create Project instance from API response"""
        project = cls(
            project_id=data['project_id'],
            org_name=data['organization_name'],
            name=data['name'],
            description=data.get('description', ''),
            created_at=Job._parse_datetime(data.get('created_at')),
            spider_count=data.get('spider_count', 0),
            job_count=data.get('job_count', 0)
        )

        headers = ["ID", "Org Name", "Name", "Description", "Created At", "Spider Count", "Job Count"]
        row_data = [
            project.project_id,
            project.org_name,
            project.name,
            project.description or "N/A",
            project.created_at.strftime("%Y-%m-%d %H:%M:%S") if project.created_at else "N/A",
            project.spider_count,
            project.job_count
        ]

        print("PROJECT DETAILS")
        print(tabulate([row_data], headers=headers, tablefmt="grid"))
        return project
