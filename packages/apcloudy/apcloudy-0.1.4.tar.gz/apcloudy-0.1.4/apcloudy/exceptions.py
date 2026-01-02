"""APCloudy specific exceptions"""


class APCloudyException(Exception):
    """Base exception for APCloudy operations"""
    pass


class APIError(APCloudyException):
    """Raised when API returns an error response"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class AuthenticationError(APIError):
    """Raised when authentication fails"""
    pass


class JobNotFoundError(APIError):
    """Raised when a job is not found"""
    pass


class ProjectNotFoundError(APIError):
    """Raised when a project is not found"""
    pass


class SpiderNotFoundError(APIError):
    """Raised when a spider is not found"""
    pass


class RateLimitError(APIError):
    """Raised when rate limit is exceeded"""
    pass
