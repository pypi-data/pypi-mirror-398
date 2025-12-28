"""
Arato SDK for Python
"""

__version__ = "1.0.0"

from .client import AratoClient, AsyncAratoClient
from .exceptions import (
    AratoAPIError,
    APIConnectionError,
    BadRequestError,
    AuthenticationError,
    NotFoundError,
    InternalServerError,
)

__all__ = [
    "AratoClient",
    "AsyncAratoClient",
    "AratoAPIError",
    "APIConnectionError",
    "BadRequestError",
    "AuthenticationError",
    "NotFoundError",
    "InternalServerError",
]
