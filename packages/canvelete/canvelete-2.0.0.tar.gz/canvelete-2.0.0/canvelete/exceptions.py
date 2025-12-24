"""Custom exceptions for the Canvelete SDK."""


class CanveleteError(Exception):
    """Base exception for all Canvelete SDK errors."""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(CanveleteError):
    """Raised when authentication fails."""
    pass


class ValidationError(CanveleteError):
    """Raised when request validation fails."""
    pass


class NotFoundError(CanveleteError):
    """Raised when a resource is not found."""
    pass


class RateLimitError(CanveleteError):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message, retry_after=None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ServerError(CanveleteError):
    """Raised when the server returns a 5xx error."""
    pass


class InsufficientScopeError(CanveleteError):
    """Raised when the required OAuth scope is missing."""
    pass
