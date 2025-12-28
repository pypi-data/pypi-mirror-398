"""Unit tests for the Arato client."""
import os
import pytest
from unittest.mock import Mock, patch
import httpx

from arato_client import AratoClient, AsyncAratoClient


class TestAratoClient:
    """Tests for the synchronous Arato client."""

    def test_client_initialization_with_api_key(self):
        """Test client initialization with explicit API key."""
        client = AratoClient(api_key="test_key_123")
        assert client._api_key == "test_key_123"

    def test_client_initialization_from_env(self):
        """Test client initialization from environment variable."""
        with patch.dict(os.environ, {"ARATO_API_KEY": "env_key_456"}):
            client = AratoClient()
            assert client._api_key == "env_key_456"

    def test_client_initialization_no_api_key(self):
        """Test that client raises error when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not provided"):
                AratoClient()

    def test_client_custom_base_url(self):
        """Test client initialization with custom base URL."""
        custom_url = "https://custom.api.com/v1"
        client = AratoClient(api_key="test_key", base_url=custom_url)
        assert str(client._base_url) == custom_url

    def test_client_custom_timeout(self):
        """Test client initialization with custom timeout."""
        client = AratoClient(api_key="test_key", timeout=120.0)
        assert client._timeout == 120.0

    def test_client_custom_retries(self):
        """Test client initialization with custom max retries."""
        client = AratoClient(api_key="test_key", max_retries=5)
        assert client._max_retries == 5

    def test_client_has_notebooks_resource(self):
        """Test that client has notebooks resource."""
        client = AratoClient(api_key="test_key")
        assert hasattr(client, "notebooks")
        assert client.notebooks is not None

    def test_client_has_datasets_resource(self):
        """Test that client has datasets resource."""
        client = AratoClient(api_key="test_key")
        assert hasattr(client, "datasets")
        assert client.datasets is not None

    def test_auth_headers(self):
        """Test that authorization headers are correctly formatted."""
        client = AratoClient(api_key="test_key_789")
        headers = client._auth_headers
        assert headers["Authorization"] == "Bearer test_key_789"

    @patch('arato_client.client.httpx.Client')
    def test_client_request_method(self, mock_http_client_class):
        """Test that client can make requests."""
        mock_http_instance = Mock()
        mock_http_client_class.return_value = mock_http_instance
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_http_instance.request.return_value = mock_response
        
        client = AratoClient(api_key="test_key")
        response = client._request("GET", "/test")
        
        assert response.status_code == 200
        mock_http_instance.request.assert_called_once()


class TestAsyncAratoClient:
    """Tests for the asynchronous Arato client."""

    def test_async_client_initialization_with_api_key(self):
        """Test async client initialization with explicit API key."""
        client = AsyncAratoClient(api_key="async_key_123")
        assert client._api_key == "async_key_123"

    def test_async_client_initialization_from_env(self):
        """Test async client initialization from environment variable."""
        with patch.dict(os.environ, {"ARATO_API_KEY": "async_env_key"}):
            client = AsyncAratoClient()
            assert client._api_key == "async_env_key"

    def test_async_client_initialization_no_api_key(self):
        """Test that async client raises error when no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key not provided"):
                AsyncAratoClient()

    def test_async_client_has_notebooks_resource(self):
        """Test that async client has notebooks resource."""
        client = AsyncAratoClient(api_key="test_key")
        assert hasattr(client, "notebooks")
        assert client.notebooks is not None

    def test_async_client_has_datasets_resource(self):
        """Test that async client has datasets resource."""
        client = AsyncAratoClient(api_key="test_key")
        assert hasattr(client, "datasets")
        assert client.datasets is not None

    @pytest.mark.asyncio
    @patch('arato_client.client.httpx.AsyncClient')
    async def test_async_client_request_method(self, mock_async_http_client_class):
        """Test that async client can make requests."""
        mock_http_instance = Mock()
        mock_async_http_client_class.return_value = mock_http_instance
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_http_instance.request = mock_request
        
        client = AsyncAratoClient(api_key="test_key")
        response = await client._request("GET", "/test")
        
        assert response.status_code == 200


class TestClientContextManagers:
    """Tests for client context manager functionality."""

    @patch('arato_client.client.httpx.Client')
    def test_sync_client_context_manager(self, mock_http_client_class):
        """Test that sync client works as a context manager."""
        mock_http_instance = Mock()
        mock_http_client_class.return_value = mock_http_instance
        
        with AratoClient(api_key="test_key") as client:
            assert client is not None
            assert client._api_key == "test_key"
        
        # Verify that close was called
        mock_http_instance.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('arato_client.client.httpx.AsyncClient')
    async def test_async_client_context_manager(self, mock_async_http_client_class):
        """Test that async client works as a context manager."""
        mock_http_instance = Mock()
        mock_async_http_client_class.return_value = mock_http_instance
        
        async def mock_aclose():
            pass
        
        mock_http_instance.aclose = mock_aclose
        
        async with AsyncAratoClient(api_key="test_key") as client:
            assert client is not None
            assert client._api_key == "test_key"
