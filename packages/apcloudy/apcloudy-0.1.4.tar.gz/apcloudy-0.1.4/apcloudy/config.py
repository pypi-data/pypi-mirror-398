"""
Configuration settings for the APCloudy client.

This module provides a `Config` class that encapsulates all the configuration
settings required for interacting with the APCloudy client. These settings
include API-related configurations, job-specific defaults, HTTP connection
options, pagination limits, file upload constraints, and logging preferences.
"""


class Config:
    """Configuration class for APCloudy client settings"""

    def __init__(self):
        self.base_url = "https://appcloudy.askpablos.com/api/client"
        self.api_key = None
        self.project_id = None
        self.current_job_id = None

        # Job settings
        self.default_units = 2
        self.default_priority = 0

        # HTTP settings
        self.request_timeout = 30
        self.max_retries = 3
        self.retry_delay = 1
        self.backoff_factor = 2

        # Logging
        self.log_level = "INFO"
        self.log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    def validate(self) -> bool:
        """Validate configuration settings"""
        if not self.api_key:
            raise ValueError("API key is required. Please pass it to the client.")

        if self.default_units < 1:
            raise ValueError("Default units must be at least 1")

        if self.request_timeout <= 0:
            raise ValueError("Request timeout must be positive")

        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")

        return True


# Global configuration instance
config = Config()
