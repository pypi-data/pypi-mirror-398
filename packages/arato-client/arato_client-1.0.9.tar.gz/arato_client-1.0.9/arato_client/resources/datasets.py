"""Dataset resource classes for API clients."""
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import Tags
from .base import AsyncBaseResource, BaseResource

if TYPE_CHECKING:
    from ..client import AratoClient, AsyncAratoClient # noqa: F401


# --- Global Datasets ---
class GlobalDatasetsResource(BaseResource):
    """Handles operations related to global datasets."""

    def list(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve a list of all global datasets."""
        return self._get("/datasets")

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
        content: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new global dataset.

        Args:
            name: Name of the dataset.
            description: Optional description.
            tags: Optional tags.
            content: Array of data objects.

        Returns:
            The created dataset object.
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if content:
            payload["content"] = content
        return self._post("/datasets", json=payload)

    def retrieve(self, dataset_id: str) -> Dict[str, Any]:
        """Retrieve a specific global dataset by ID."""
        return self._get(f"/datasets/{dataset_id}")


class AsyncGlobalDatasetsResource(AsyncBaseResource):
    """Handles async operations related to global datasets."""

    async def list(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve a list of all global datasets."""
        return await self._get("/datasets")

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
        content: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new global dataset.

        Args:
            name: Name of the dataset.
            description: Optional description.
            tags: Optional tags.
            content: Array of data objects.

        Returns:
            The created dataset object.
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if content:
            payload["content"] = content
        return await self._post("/datasets", json=payload)

    async def retrieve(self, dataset_id: str) -> Dict[str, Any]:
        """Retrieve a specific global dataset by ID."""
        return await self._get(f"/datasets/{dataset_id}")


# --- Notebook-Scoped Datasets ---
class NotebookDatasetsResource(BaseResource):
    """Handles operations for datasets within a specific notebook."""

    def list(self, *, notebook_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve all datasets for a specific notebook."""
        return self._get(f"/notebooks/{notebook_id}/datasets")

    def create(
        self,
        *,
        notebook_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
        content: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new dataset within a specific notebook."""
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if content:
            payload["content"] = content
        return self._post(f"/notebooks/{notebook_id}/datasets", json=payload)

    def retrieve(self, *, notebook_id: str, dataset_id: str) -> Dict[str, Any]:
        """Retrieve a specific dataset from a notebook."""
        return self._get(f"/notebooks/{notebook_id}/datasets/{dataset_id}")


class AsyncNotebookDatasetsResource(AsyncBaseResource):
    """Handles async operations for datasets within a specific notebook."""

    async def list(self, *, notebook_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve all datasets for a specific notebook."""
        return await self._get(f"/notebooks/{notebook_id}/datasets")

    async def create(
        self,
        *,
        notebook_id: str,
        name: str,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
        content: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new dataset within a specific notebook."""
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        if content:
            payload["content"] = content
        return await self._post(f"/notebooks/{notebook_id}/datasets", json=payload)

    async def retrieve(self, *, notebook_id: str, dataset_id: str) -> Dict[str, Any]:
        """Retrieve a specific dataset from a notebook."""
        return await self._get(f"/notebooks/{notebook_id}/datasets/{dataset_id}")
