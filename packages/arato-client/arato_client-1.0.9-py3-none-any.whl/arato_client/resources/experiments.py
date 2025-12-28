"""Experiment resource classes for API clients."""
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models import PromptConfig
from .base import AsyncBaseResource, BaseResource
from .runs import AsyncRunsResource, RunsResource
from .evals import AsyncEvalsResource, EvalsResource

if TYPE_CHECKING:
    from ..client import AratoClient, AsyncAratoClient


class ExperimentsResource(BaseResource):
    """Handles operations related to experiments within a notebook."""

    def __init__(self, client: "AratoClient"):
        super().__init__(client)
        self.runs = RunsResource(client)
        self.evals = EvalsResource(client)

    def list(self, *, notebook_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all experiments for a specific notebook."""
        return self._get(f"/notebooks/{notebook_id}/experiments")

    def create(
        self,
        *,
        notebook_id: str,
        name: str,
        prompt_config: PromptConfig,
        description: Optional[str] = None,
        prompt_type: str = "generating_prompt",
        color_index: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new experiment in a notebook."""
        payload = {
            "name": name,
            "prompt_config": prompt_config,
            "prompt_type": prompt_type,
        }
        if description is not None:
            payload["description"] = description
        if color_index is not None:
            payload["color_index"] = color_index
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        return self._post(f"/notebooks/{notebook_id}/experiments", json=payload)

    def retrieve(self, *, notebook_id: str, experiment_id: str) -> Dict[str, Any]:
        """Retrieve a specific experiment."""
        return self._get(f"/notebooks/{notebook_id}/experiments/{experiment_id}")

    def update(
        self,
        *,
        notebook_id: str,
        experiment_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_config: Optional[PromptConfig] = None,
        color_index: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing experiment."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if prompt_config is not None:
            payload["prompt_config"] = prompt_config
        if color_index is not None:
            payload["color_index"] = color_index
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        return self._put(f"/notebooks/{notebook_id}/experiments/{experiment_id}", json=payload)


class AsyncExperimentsResource(AsyncBaseResource):
    """Handles async operations related to experiments within a notebook."""

    def __init__(self, client: "AsyncAratoClient"):
        super().__init__(client)
        self.runs = AsyncRunsResource(client)
        self.evals = AsyncEvalsResource(client)

    async def list(self, *, notebook_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """List all experiments for a specific notebook."""
        return await self._get(f"/notebooks/{notebook_id}/experiments")

    async def create(
        self,
        *,
        notebook_id: str,
        name: str,
        prompt_config: PromptConfig,
        description: Optional[str] = None,
        prompt_type: str = "generating_prompt",
        color_index: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new experiment in a notebook."""
        payload = {
            "name": name,
            "prompt_config": prompt_config,
            "prompt_type": prompt_type,
        }
        if description is not None:
            payload["description"] = description
        if color_index is not None:
            payload["color_index"] = color_index
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        return await self._post(f"/notebooks/{notebook_id}/experiments", json=payload)

    async def retrieve(self, *, notebook_id: str, experiment_id: str) -> Dict[str, Any]:
        """Retrieve a specific experiment."""
        return await self._get(f"/notebooks/{notebook_id}/experiments/{experiment_id}")

    async def update(
        self,
        *,
        notebook_id: str,
        experiment_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        prompt_config: Optional[PromptConfig] = None,
        color_index: Optional[int] = None,
        dataset_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing experiment."""
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if prompt_config is not None:
            payload["prompt_config"] = prompt_config
        if color_index is not None:
            payload["color_index"] = color_index
        if dataset_id is not None:
            payload["dataset_id"] = dataset_id
        return await self._put(
            f"/notebooks/{notebook_id}/experiments/{experiment_id}",
            json=payload
        )
