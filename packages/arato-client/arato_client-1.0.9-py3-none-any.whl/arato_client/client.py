"""Arato API client module."""
import os
from typing import Optional, Union

import httpx
from httpx import Timeout

from .resources.notebooks import AsyncNotebooksResource, NotebooksResource
from .resources.datasets import AsyncGlobalDatasetsResource, GlobalDatasetsResource
from .exceptions import APIConnectionError

# Default values
DEFAULT_BASE_URL = "https://api.arato.ai/api/v1"
DEFAULT_TIMEOUT = 60.0  # 60 seconds
DEFAULT_MAX_RETRIES = 2


class _BaseClient:
    """Base for sync and async clients, handling common initialization."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Union[float, Timeout, None] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initializes the base client.

        Args:
            api_key: The Arato API key. Defaults to ARATO_API_KEY env var.
            base_url: The base URL for the API. Defaults to production URL.
            timeout: The request timeout.
            max_retries: The maximum number of retries for transient errors.

        Raises:
            ValueError: If the API key is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("ARATO_API_KEY")
        if api_key is None:
            raise ValueError(
                "API key not provided. Pass it to the client or set "
                "the ARATO_API_KEY environment variable."
            )

        self._api_key = api_key
        self._base_url = httpx.URL(base_url or DEFAULT_BASE_URL)
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}"}


class AratoClient(_BaseClient):
    """
    Synchronous client for the Arato API.

    Provides access to all API resources through convenient attributes.
    """

    _client: httpx.Client

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Union[float, Timeout, None] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
    ):
        """
        Initialize the synchronous Arato client.

        Args:
            api_key: The Arato API key.
            base_url: The base URL for the API.
            timeout: The request timeout.
            max_retries: Maximum number of retries.
            http_client: An optional external httpx.Client to use.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )

        if http_client:
            self._client = http_client
        else:
            self._client = httpx.Client(
                base_url=self._base_url,
                headers=self._auth_headers,
                timeout=self._timeout,
                transport=httpx.HTTPTransport(retries=self._max_retries),
            )

        # Initialize resources
        self.notebooks = NotebooksResource(self)
        self.datasets = GlobalDatasetsResource(self)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the underlying HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """
        Makes a raw HTTP request.

        Args:
            method: HTTP method (e.g., "GET", "POST").
            path: API endpoint path.
            **kwargs: Additional arguments for httpx.Client.request.

        Returns:
            The httpx.Response object.

        Raises:
            APIConnectionError: If a connection error occurs.
        """
        try:
            return self._client.request(method, path, **kwargs)
        except httpx.RequestError as e:
            raise APIConnectionError(f"Error connecting to Arato API: {e}") from e


class AsyncAratoClient(_BaseClient):
    """
    Asynchronous client for the Arato API.

    Provides access to all API resources through convenient attributes.
    """

    _client: httpx.AsyncClient

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Union[float, Timeout, None] = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        """
        Initialize the asynchronous Arato client.

        Args:
            api_key: The Arato API key.
            base_url: The base URL for the API.
            timeout: The request timeout.
            max_retries: Maximum number of retries.
            http_client: An optional external httpx.AsyncClient to use.
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries
        )

        if http_client:
            self._client = http_client
        else:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=self._auth_headers,
                timeout=self._timeout,
                transport=httpx.AsyncHTTPTransport(retries=self._max_retries),
            )

        # Initialize resources
        self.notebooks = AsyncNotebooksResource(self)
        self.datasets = AsyncGlobalDatasetsResource(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the underlying HTTP client."""
        if hasattr(self, "_client"):
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """
        Makes a raw async HTTP request.

        Args:
            method: HTTP method (e.g., "GET", "POST").
            path: API endpoint path.
            **kwargs: Additional arguments for httpx.AsyncClient.request.

        Returns:
            The httpx.Response object.

        Raises:
            APIConnectionError: If a connection error occurs.
        """
        try:
            return await self._client.request(method, path, **kwargs)
        except httpx.RequestError as e:
            raise APIConnectionError(f"Error connecting to Arato API: {e}") from e
