"""Datasets resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..types.common import PaginatedResponse
from ..types.datasets import Dataset, DatasetCreate, DatasetPrompt

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class DatasetsResource:
    """Sync resource for datasets."""

    def __init__(self, client: SyncHTTPClient):
        self._client = client

    def create(
        self,
        name: str,
        prompts: list[dict[str, Any]],
        *,
        description: str | None = None,
        project_id: str | None = None,
    ) -> Dataset:
        """Create a new dataset.

        Args:
            name: Dataset name
            prompts: List of prompts with id, messages, and optional category
            description: Optional description
            project_id: Optional project ID to associate with

        Returns:
            The created dataset
        """
        prompt_models = [DatasetPrompt.model_validate(p) for p in prompts]
        data = DatasetCreate(
            name=name,
            prompts=prompt_models,
            description=description,
            projectId=project_id,
        )
        response = self._client.post(
            "/datasets", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Dataset.model_validate(response.get("dataset"))

    def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Dataset]:
        """List all datasets with pagination.

        Args:
            project_id: Optional filter by project ID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20, max: 100)

        Returns:
            Paginated list of datasets
        """
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = self._client.get("/datasets", params=params or None)
        datasets = [Dataset.model_validate(d) for d in response.get("datasets", [])]
        return PaginatedResponse[Dataset](
            items=datasets,
            total=response.get("total", len(datasets)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(datasets)),
            hasMore=response.get("hasMore", False),
        )

    def get(self, dataset_id: str) -> Dataset:
        """Get a dataset by ID.

        Args:
            dataset_id: Dataset ID

        Returns:
            The dataset with prompts
        """
        response = self._client.get(f"/datasets/{dataset_id}")
        return Dataset.model_validate(response.get("dataset"))

    def delete(self, dataset_id: str) -> bool:
        """Delete a dataset.

        Args:
            dataset_id: Dataset ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/datasets/{dataset_id}")
        return True


class AsyncDatasetsResource:
    """Async resource for datasets."""

    def __init__(self, client: AsyncHTTPClient):
        self._client = client

    async def create(
        self,
        name: str,
        prompts: list[dict[str, Any]],
        *,
        description: str | None = None,
        project_id: str | None = None,
    ) -> Dataset:
        """Create a new dataset."""
        prompt_models = [DatasetPrompt.model_validate(p) for p in prompts]
        data = DatasetCreate(
            name=name,
            prompts=prompt_models,
            description=description,
            projectId=project_id,
        )
        response = await self._client.post(
            "/datasets", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Dataset.model_validate(response.get("dataset"))

    async def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Dataset]:
        """List all datasets with pagination."""
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = await self._client.get("/datasets", params=params or None)
        datasets = [Dataset.model_validate(d) for d in response.get("datasets", [])]
        return PaginatedResponse[Dataset](
            items=datasets,
            total=response.get("total", len(datasets)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(datasets)),
            hasMore=response.get("hasMore", False),
        )

    async def get(self, dataset_id: str) -> Dataset:
        """Get a dataset by ID."""
        response = await self._client.get(f"/datasets/{dataset_id}")
        return Dataset.model_validate(response.get("dataset"))

    async def delete(self, dataset_id: str) -> bool:
        """Delete a dataset."""
        await self._client.delete(f"/datasets/{dataset_id}")
        return True
