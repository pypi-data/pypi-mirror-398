"""Base resource classes for API clients."""
from typing import TYPE_CHECKING, Any, Dict

from ..exceptions import _handle_api_error

if TYPE_CHECKING:
    from ..client import AratoClient, AsyncAratoClient


class BaseResource:
    """Base class for all API resource clients."""

    def __init__(self, client: "AratoClient"):
        self._client = client

    def _get(self, path: str, params: Dict[str, Any] = None) -> Any:
        response = self._client._request("GET", path, params=params) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    def _post(self, path: str, json: Dict[str, Any]) -> Any:
        response = self._client._request("POST", path, json=json) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    def _put(self, path: str, json: Dict[str, Any]) -> Any:
        response = self._client._request("PUT", path, json=json) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    def _delete(self, path: str) -> None:
        response = self._client._request("DELETE", path) # pylint: disable=protected-access
        _handle_api_error(response)


class AsyncBaseResource:
    """Async base class for all API resource clients."""

    def __init__(self, client: "AsyncAratoClient"):
        self._client = client

    async def _get(self, path: str, params: Dict[str, Any] = None) -> Any:
        response = await self._client._request("GET", path, params=params) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    async def _post(self, path: str, json: Dict[str, Any]) -> Any:
        response = await self._client._request("POST", path, json=json) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    async def _put(self, path: str, json: Dict[str, Any]) -> Any:
        response = await self._client._request("PUT", path, json=json) # pylint: disable=protected-access
        _handle_api_error(response)
        return response.json()

    async def _delete(self, path: str) -> None:
        response = await self._client._request("DELETE", path) # pylint: disable=protected-access
        _handle_api_error(response)
