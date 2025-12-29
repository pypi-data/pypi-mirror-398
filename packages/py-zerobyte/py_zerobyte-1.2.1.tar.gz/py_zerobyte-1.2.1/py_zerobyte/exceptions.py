"""Custom exceptions for Zerobyte SDK."""


class ZerobyteError(Exception):
    """Base exception for all Zerobyte SDK errors."""
    pass


class AuthenticationError(ZerobyteError):
    """Raised when authentication fails."""
    pass


class APIError(ZerobyteError):
    """Raised when the API returns an error."""
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""
    pass


class ValidationError(APIError):
    """Raised when request validation fails."""
    pass
