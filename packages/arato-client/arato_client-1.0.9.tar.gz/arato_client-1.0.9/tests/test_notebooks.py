"""Unit tests for notebook resource operations."""
import pytest
from unittest.mock import Mock, patch
import httpx

from arato_client import AratoClient, AsyncAratoClient
from arato_client.exceptions import AratoAPIError


@pytest.fixture
def mock_client():
    """Create a mock synchronous client."""
    client = Mock(spec=AratoClient)
    client._request = Mock()
    return client


@pytest.fixture
def mock_async_client():
    """Create a mock asynchronous client."""
    client = Mock(spec=AsyncAratoClient)
    client._request = Mock()
    return client


class TestNotebooksResource:
    """Tests for synchronous notebook operations."""

    def test_list_notebooks(self, mock_client):
        """Test listing notebooks."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "nb_123", "name": "Test Notebook 1"},
                {"id": "nb_456", "name": "Test Notebook 2"}
            ]
        }
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        result = notebooks.list()
        
        mock_client._request.assert_called_once_with("GET", "/notebooks", params=None)
        assert "data" in result
        assert len(result["data"]) == 2

    def test_create_notebook(self, mock_client):
        """Test creating a notebook."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "nb_123",
            "name": "New Notebook",
            "description": "Test description"
        }
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        result = notebooks.create(
            name="New Notebook",
            description="Test description",
            tags=["test", "demo"]
        )
        
        mock_client._request.assert_called_once()
        call_args = mock_client._request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "/notebooks"
        assert call_args[1]["json"]["name"] == "New Notebook"
        assert call_args[1]["json"]["description"] == "Test description"
        assert call_args[1]["json"]["tags"] == ["test", "demo"]
        assert result["id"] == "nb_123"

    def test_create_notebook_minimal(self, mock_client):
        """Test creating a notebook with minimal parameters."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "nb_123",
            "name": "Minimal Notebook"
        }
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        result = notebooks.create(name="Minimal Notebook")
        
        call_args = mock_client._request.call_args
        assert "description" not in call_args[1]["json"]
        assert "tags" not in call_args[1]["json"]

    def test_retrieve_notebook(self, mock_client):
        """Test retrieving a specific notebook."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "nb_123",
            "name": "Test Notebook",
            "description": "A test notebook"
        }
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        result = notebooks.retrieve("nb_123")
        
        mock_client._request.assert_called_once_with("GET", "/notebooks/nb_123", params=None)
        assert result["id"] == "nb_123"
        assert result["name"] == "Test Notebook"

    def test_delete_notebook(self, mock_client):
        """Test deleting a notebook."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        result = notebooks.delete("nb_123")
        
        mock_client._request.assert_called_once_with("DELETE", "/notebooks/nb_123")
        assert result is None

    def test_delete_notebook_not_found(self, mock_client):
        """Test deleting a non-existent notebook."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Notebook not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            notebooks.delete("nb_nonexistent")

    def test_delete_notebook_forbidden(self, mock_client):
        """Test deleting a notebook without permissions."""
        from arato_client.resources.notebooks import NotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=Mock(), response=mock_response
        )
        mock_client._request.return_value = mock_response
        
        notebooks = NotebooksResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            notebooks.delete("nb_123")


class TestAsyncNotebooksResource:
    """Tests for asynchronous notebook operations."""

    @pytest.mark.asyncio
    async def test_list_notebooks_async(self, mock_async_client):
        """Test listing notebooks asynchronously."""
        from arato_client.resources.notebooks import AsyncNotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": "nb_123", "name": "Test Notebook 1"},
                {"id": "nb_456", "name": "Test Notebook 2"}
            ]
        }
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_async_client._request = mock_request
        
        notebooks = AsyncNotebooksResource(mock_async_client)
        result = await notebooks.list()
        
        assert "data" in result
        assert len(result["data"]) == 2

    @pytest.mark.asyncio
    async def test_create_notebook_async(self, mock_async_client):
        """Test creating a notebook asynchronously."""
        from arato_client.resources.notebooks import AsyncNotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": "nb_123",
            "name": "New Async Notebook"
        }
        
        request_args = []
        
        async def mock_request(*args, **kwargs):
            request_args.append((args, kwargs))
            return mock_response
        
        mock_async_client._request = mock_request
        
        notebooks = AsyncNotebooksResource(mock_async_client)
        result = await notebooks.create(name="New Async Notebook")
        
        assert len(request_args) == 1
        assert request_args[0][0][0] == "POST"
        assert result["id"] == "nb_123"

    @pytest.mark.asyncio
    async def test_retrieve_notebook_async(self, mock_async_client):
        """Test retrieving a notebook asynchronously."""
        from arato_client.resources.notebooks import AsyncNotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "nb_789",
            "name": "Async Notebook"
        }
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_async_client._request = mock_request
        
        notebooks = AsyncNotebooksResource(mock_async_client)
        result = await notebooks.retrieve("nb_789")
        
        assert result["id"] == "nb_789"

    @pytest.mark.asyncio
    async def test_delete_notebook_async(self, mock_async_client):
        """Test deleting a notebook asynchronously."""
        from arato_client.resources.notebooks import AsyncNotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        
        request_args = []
        
        async def mock_request(*args, **kwargs):
            request_args.append((args, kwargs))
            return mock_response
        
        mock_async_client._request = mock_request
        
        notebooks = AsyncNotebooksResource(mock_async_client)
        result = await notebooks.delete("nb_123")
        
        assert len(request_args) == 1
        assert request_args[0][0][0] == "DELETE"
        assert request_args[0][0][1] == "/notebooks/nb_123"
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_notebook_not_found_async(self, mock_async_client):
        """Test deleting a non-existent notebook asynchronously."""
        from arato_client.resources.notebooks import AsyncNotebooksResource
        
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Notebook not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_async_client._request = mock_request
        
        notebooks = AsyncNotebooksResource(mock_async_client)
        
        with pytest.raises(AratoAPIError):
            await notebooks.delete("nb_nonexistent")


class TestNotebookIntegration:
    """Integration tests using a full client instance."""

    @patch('arato_client.client.httpx.Client')
    def test_full_delete_flow(self, mock_http_client_class):
        """Test the full delete flow with a real client instance."""
        mock_http_instance = Mock()
        mock_http_client_class.return_value = mock_http_instance
        
        # Mock successful delete response
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_http_instance.request.return_value = mock_response
        
        client = AratoClient(api_key="test_key")
        client.notebooks.delete("nb_123")
        
        # Verify the request was made correctly
        mock_http_instance.request.assert_called_once()
        call_args = mock_http_instance.request.call_args
        assert call_args[0][0] == "DELETE"
        assert "/notebooks/nb_123" in str(call_args)
