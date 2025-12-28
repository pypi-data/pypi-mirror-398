"""Run resource classes for API clients."""
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import APIKeys
from .base import AsyncBaseResource, BaseResource

if TYPE_CHECKING:
    from ..client import AratoClient, AsyncAratoClient # noqa: F401


class RunsResource(BaseResource):
    """Handles operations related to experiment runs."""

    def list(self, *, notebook_id: str, experiment_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all runs for a specific experiment."""
        return self._get(f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs")

    def create(
        self,
        *,
        notebook_id: str,
        experiment_id: str,
        api_keys: APIKeys,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and execute a run for an experiment.

        Args:
            notebook_id: The ID of the notebook.
            experiment_id: The ID of the experiment.
            api_keys: API keys for AI model providers (e.g., {"openai_api_key": "..."}).
            callback_url: Optional webhook URL to receive run status updates.

        Returns:
            The created run object.
        """
        payload = {"api_keys": api_keys}
        if callback_url:
            payload["callback_url"] = callback_url
        return self._post(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs",
            json=payload
        )

    def retrieve(
        self, *, notebook_id: str, experiment_id: str, run_id: str
    ) -> Dict[str, Any]:
        """Retrieve a specific run by ID."""
        return self._get(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs/{run_id}"
        )


class AsyncRunsResource(AsyncBaseResource):
    """Handles async operations related to experiment runs."""

    async def list(
        self, *, notebook_id: str, experiment_id: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List all runs for a specific experiment."""
        return await self._get(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs"
        )

    async def create(
        self,
        *,
        notebook_id: str,
        experiment_id: str,
        api_keys: APIKeys,
        callback_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create and execute a run for an experiment.

        Args:
            notebook_id: The ID of the notebook.
            experiment_id: The ID of the experiment.
            api_keys: API keys for AI model providers (e.g., {"openai_api_key": "..."}).
            callback_url: Optional webhook URL to receive run status updates.

        Returns:
            The created run object.
        """
        payload = {"api_keys": api_keys}
        if callback_url:
            payload["callback_url"] = callback_url
        return await self._post(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs",
            json=payload
        )

    async def retrieve(
        self, *, notebook_id: str, experiment_id: str, run_id: str
    ) -> Dict[str, Any]:
        """Retrieve a specific run by ID."""
        return await self._get(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}/runs/{run_id}"
        )
