# APCloudy

[![PyPI version](https://badge.fury.io/py/apcloudy.svg)](https://badge.fury.io/py/apcloudy)
[![Python versions](https://img.shields.io/pypi/pyversions/apcloudy.svg)](https://pypi.org/project/apcloudy/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/apcloudy/badge/?version=latest)](https://apcloudy.readthedocs.io/en/latest/?badge=latest)
[![Downloads](https://pepy.tech/badge/apcloudy)](https://pepy.tech/project/apcloudy)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python client library for interacting with the APCloudy platform. This library provides a simple and intuitive interface for managing projects, spiders, and jobs on the APCloudy web scraping platform.

## 📚 Documentation

Complete documentation is available at **[apcloudy.readthedocs.io](https://apcloudy.readthedocs.io/)**

## Features

- **Project Management**: Create, update, and manage your APCloudy projects
- **Spider Management**: Deploy and manage web scraping spiders
- **Job Management**: Start, monitor, and manage scraping jobs
- **Authentication**: Secure API key-based authentication
- **Error Handling**: Comprehensive error handling with custom exceptions
- **Rate Limiting**: Built-in rate limiting support

## Installation

Install apcloudy using pip:

```bash
pip install apcloudy
```

## Quick Start

```python
from apcloudy import APCloudyClient

# Initialize the client with your API key
client = APCloudyClient("your-api-key-here")

# Get all projects
projects = client.get_projects()

# Get a specific project
project = client.get_project("project-id")

# List spiders in a project
spiders = client.get_spiders("project-id")

# Start a job
job = client.start_job("project-id", "spider-name")

# Get job status
job_status = client.get_job("job-id")
```

## API Reference

### APCloudyClient

The main client class for interacting with the APCloudy API.

#### Methods

- `get_projects()`: List all projects
- `get_project(project_id)`: Get a specific project
- `get_spiders(project_id)`: List spiders in a project
- `get_spider(project_id, spider_name)`: Get a specific spider
- `start_job(project_id, spider_name, **kwargs)`: Start a new job
- `get_job(job_id)`: Get job details
- `get_jobs(project_id)`: List jobs for a project
- `stop_job(job_id)`: Stop a running job

### Models

- `Project`: Represents an APCloudy project
- `Spider`: Represents a spider within a project
- `Job`: Represents a scraping job
- `JobState`: Enumeration of possible job states

### Exceptions

- `APIError`: Base exception for API errors
- `AuthenticationError`: Raised when authentication fails
- `ProjectNotFoundError`: Raised when a project is not found
- `SpiderNotFoundError`: Raised when a spider is not found
- `JobNotFoundError`: Raised when a job is not found
- `RateLimitError`: Raised when rate limits are exceeded

## Development

### Installing for Development

```bash
git clone https://github.com/yourusername/apcloudy.git
cd apcloudy
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black apcloudy/
flake8 apcloudy/
```

### Type Checking

```bash
mypy apcloudy/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub repository](https://github.com/fawadss1/apcloudy/issues).


[Unreleased]: https://github.com/fawadss1/apcloudy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fawadss1/apcloudy/releases/tag/v0.1.0
