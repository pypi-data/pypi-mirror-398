"""Custom exceptions for Callbotics SDK"""


class CallboticsException(Exception):
    """Base exception for all Callbotics SDK errors"""
    pass


class AuthenticationError(CallboticsException):
    """Raised when authentication fails"""
    pass


class APIError(CallboticsException):
    """Raised when API returns an error response"""

    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class ResourceNotFoundError(APIError):
    """Raised when a requested resource is not found"""
    pass


class ValidationError(CallboticsException):
    """Raised when request validation fails"""
    pass


class ConfigurationError(CallboticsException):
    """Raised when configuration is invalid or incomplete"""
    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded"""
    pass
