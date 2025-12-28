"""Unit tests for base resource classes."""
import pytest
from unittest.mock import Mock
import httpx

from arato_client.resources.base import BaseResource, AsyncBaseResource
from arato_client.exceptions import AratoAPIError


@pytest.fixture
def mock_client():
    """Create a mock client."""
    client = Mock()
    client._request = Mock()
    return client


class TestBaseResource:
    """Tests for BaseResource class."""

    def test_get_request(self, mock_client):
        """Test _get method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        result = resource._get("/test/path")
        
        mock_client._request.assert_called_once_with("GET", "/test/path", params=None)
        assert result == {"data": "test"}

    def test_get_request_with_params(self, mock_client):
        """Test _get method with query parameters."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        params = {"limit": 10, "offset": 0}
        result = resource._get("/test/path", params=params)
        
        mock_client._request.assert_called_once_with("GET", "/test/path", params=params)
        assert result == {"data": "test"}

    def test_post_request(self, mock_client):
        """Test _post method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "name": "test"}
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        payload = {"name": "test"}
        result = resource._post("/test/path", json=payload)
        
        mock_client._request.assert_called_once_with("POST", "/test/path", json=payload)
        assert result == {"id": "123", "name": "test"}

    def test_put_request(self, mock_client):
        """Test _put method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "updated"}
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        payload = {"name": "updated"}
        result = resource._put("/test/path", json=payload)
        
        mock_client._request.assert_called_once_with("PUT", "/test/path", json=payload)
        assert result == {"id": "123", "name": "updated"}

    def test_delete_request(self, mock_client):
        """Test _delete method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        result = resource._delete("/test/path/123")
        
        mock_client._request.assert_called_once_with("DELETE", "/test/path/123")
        assert result is None

    def test_delete_request_error(self, mock_client):
        """Test _delete method with error response."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Not found"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            resource._delete("/test/path/123")

    def test_api_error_handling(self, mock_client):
        """Test that API errors are properly raised."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=Mock(), response=mock_response
        )
        mock_client._request.return_value = mock_response
        
        resource = BaseResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            resource._get("/test/path")


class TestAsyncBaseResource:
    """Tests for AsyncBaseResource class."""

    @pytest.mark.asyncio
    async def test_get_request_async(self, mock_client):
        """Test async _get method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        result = await resource._get("/test/path")
        
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_post_request_async(self, mock_client):
        """Test async _post method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123", "name": "test"}
        
        request_args = []
        
        async def mock_request(*args, **kwargs):
            request_args.append((args, kwargs))
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        payload = {"name": "test"}
        result = await resource._post("/test/path", json=payload)
        
        assert len(request_args) == 1
        assert request_args[0][0][0] == "POST"
        assert request_args[0][0][1] == "/test/path"
        assert request_args[0][1]["json"] == payload
        assert result == {"id": "123", "name": "test"}

    @pytest.mark.asyncio
    async def test_put_request_async(self, mock_client):
        """Test async _put method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "updated"}
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        payload = {"name": "updated"}
        result = await resource._put("/test/path", json=payload)
        
        assert result == {"id": "123", "name": "updated"}

    @pytest.mark.asyncio
    async def test_delete_request_async(self, mock_client):
        """Test async _delete method."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 204
        
        request_args = []
        
        async def mock_request(*args, **kwargs):
            request_args.append((args, kwargs))
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        result = await resource._delete("/test/path/123")
        
        assert len(request_args) == 1
        assert request_args[0][0][0] == "DELETE"
        assert request_args[0][0][1] == "/test/path/123"
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_request_error_async(self, mock_client):
        """Test async _delete method with error response."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 403
        mock_response.json.return_value = {"error": "Forbidden"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "403 Forbidden", request=Mock(), response=mock_response
        )
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            await resource._delete("/test/path/123")

    @pytest.mark.asyncio
    async def test_api_error_handling_async(self, mock_client):
        """Test that API errors are properly raised in async methods."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", request=Mock(), response=mock_response
        )
        
        async def mock_request(*args, **kwargs):
            return mock_response
        
        mock_client._request = mock_request
        
        resource = AsyncBaseResource(mock_client)
        
        with pytest.raises(AratoAPIError):
            await resource._get("/test/path")
