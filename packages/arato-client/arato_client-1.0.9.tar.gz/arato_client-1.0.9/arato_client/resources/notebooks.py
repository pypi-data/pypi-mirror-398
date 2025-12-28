"""Notebook resource classes for API clients."""
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import Tags
from .base import AsyncBaseResource, BaseResource
from .datasets import AsyncNotebookDatasetsResource, NotebookDatasetsResource
from .experiments import AsyncExperimentsResource, ExperimentsResource

if TYPE_CHECKING:
    from ..client import AratoClient, AsyncAratoClient


class NotebooksResource(BaseResource):
    """Handles operations related to notebooks."""

    def __init__(self, client: "AratoClient"):
        super().__init__(client)
        self.datasets = NotebookDatasetsResource(client)
        self.experiments = ExperimentsResource(client)

    def list(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve a list of all notebooks accessible to the authenticated user.

        Returns:
            A dictionary containing a list of notebook objects.
        """
        return self._get("/notebooks")

    def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
    ) -> Dict[str, Any]:
        """
        Create a new notebook.

        Args:
            name: Name of the notebook.
            description: Optional description of the notebook.
            tags: Optional tags for categorizing the notebook.

        Returns:
            The created notebook object.
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        return self._post("/notebooks", json=payload)

    def retrieve(self, notebook_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific notebook by ID.

        Args:
            notebook_id: The unique identifier for the notebook.

        Returns:
            The notebook object.
        """
        return self._get(f"/notebooks/{notebook_id}")

    def delete(self, notebook_id: str) -> None:
        """
        Delete a specific notebook by ID.

        Requires Owner or Editor permissions.

        Warning:
            This operation will delete:
            - The notebook itself
            - All experiments within the notebook
            - All datasets scoped to the notebook
            - All runs and evaluations associated with the notebook's experiments

        Args:
            notebook_id: The unique identifier for the notebook.

        Returns:
            None
        """
        self._delete(f"/notebooks/{notebook_id}")


class AsyncNotebooksResource(AsyncBaseResource):
    """Handles async operations related to notebooks."""

    def __init__(self, client: "AsyncAratoClient"):
        super().__init__(client)
        self.datasets = AsyncNotebookDatasetsResource(client)
        self.experiments = AsyncExperimentsResource(client)

    async def list(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve a list of all notebooks accessible to the authenticated user.

        Returns:
            A dictionary containing a list of notebook objects.
        """
        return await self._get("/notebooks")

    async def create(
        self,
        name: str,
        *,
        description: Optional[str] = None,
        tags: Optional[Tags] = None,
    ) -> Dict[str, Any]:
        """
        Create a new notebook.

        Args:
            name: Name of the notebook.
            description: Optional description of the notebook.
            tags: Optional tags for categorizing the notebook.

        Returns:
            The created notebook object.
        """
        payload = {"name": name}
        if description:
            payload["description"] = description
        if tags:
            payload["tags"] = tags
        return await self._post("/notebooks", json=payload)

    async def retrieve(self, notebook_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific notebook by ID.

        Args:
            notebook_id: The unique identifier for the notebook.

        Returns:
            The notebook object.
        """
        return await self._get(f"/notebooks/{notebook_id}")

    async def delete(self, notebook_id: str) -> None:
        """
        Delete a specific notebook by ID.

        Requires Owner or Editor permissions.

        Warning:
            This operation will delete:
            - The notebook itself
            - All experiments within the notebook
            - All datasets scoped to the notebook
            - All runs and evaluations associated with the notebook's experiments

        Args:
            notebook_id: The unique identifier for the notebook.

        Returns:
            None
        """
        await self._delete(f"/notebooks/{notebook_id}")
