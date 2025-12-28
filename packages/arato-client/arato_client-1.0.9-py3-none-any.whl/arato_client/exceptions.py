"""Arato API exceptions module."""
from typing import Optional
import httpx


class AratoAPIError(Exception):
    """Base exception for all Arato API errors."""

    def __init__(self, message: str, response: Optional[httpx.Response] = None):
        super().__init__(message)
        self.response = response
        self.message = message


class APIConnectionError(AratoAPIError):
    """Raised when there is a problem connecting to the API."""


class BadRequestError(AratoAPIError):
    """Raised for 400 Bad Request errors."""


class AuthenticationError(AratoAPIError):
    """Raised for 403 Forbidden errors (invalid API key or permissions)."""


class NotFoundError(AratoAPIError):
    """Raised for 404 Not Found errors."""


class InternalServerError(AratoAPIError):
    """Raised for 5xx internal server errors."""


def _handle_api_error(response: httpx.Response) -> None:
    """
    Checks for HTTP errors and raises the appropriate AratoAPIError.

    Args:
        response: The httpx.Response object.

    Raises:
        BadRequestError: For 400 status codes.
        AuthenticationError: For 403 status codes.
        NotFoundError: For 404 status codes.
        InternalServerError: For 5xx status codes.
        AratoAPIError: For other 4xx errors.
    """
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            # Try to parse a structured error message
            error_details = e.response.json().get("error", e.response.text)
        except (ValueError, KeyError, AttributeError):
            error_details = e.response.text or f"HTTP error {status_code}"

        message = f"API request failed with status {status_code}: {error_details}"

        if status_code == 400:
            raise BadRequestError(message, response=e.response) from e
        if status_code == 403:
            raise AuthenticationError(message, response=e.response) from e
        if status_code == 404:
            raise NotFoundError(message, response=e.response) from e
        if 500 <= status_code < 600:
            raise InternalServerError(message, response=e.response) from e

        # Fallback for other client-side errors
        raise AratoAPIError(message, response=e.response) from e
