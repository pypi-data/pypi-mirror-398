"""Zerobyte SDK - Python client for Zerobyte API."""

from .client import ZerobyteClient
from .exceptions import (
    ZerobyteError,
    AuthenticationError,
    APIError,
    NotFoundError,
    ValidationError,
)

__version__ = "1.1.0"
__all__ = [
    "ZerobyteClient",
    "ZerobyteError",
    "AuthenticationError",
    "APIError",
    "NotFoundError",
    "ValidationError",
]
