"""Checkpoints resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..types.checkpoints import Checkpoint, CheckpointCreate
from ..types.common import PaginatedResponse, TrainingMethod

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class CheckpointsResource:
    """Sync resource for model checkpoints."""

    def __init__(self, client: SyncHTTPClient):
        self._client = client

    def create(
        self,
        name: str,
        model_base: str,
        *,
        training_method: TrainingMethod | None = None,
        training_config: dict[str, Any] | None = None,
        project_id: str | None = None,
        notes: str | None = None,
    ) -> Checkpoint:
        """Register a new model checkpoint.

        Args:
            name: Checkpoint name (e.g., "llama-3.2-8b-dpo-v1")
            model_base: Base model name (e.g., "llama-3.2-8b")
            training_method: Training method used (lora, full, dpo, rlhf, other)
            training_config: Optional training configuration
            project_id: Optional project ID
            notes: Optional notes

        Returns:
            The created checkpoint
        """
        data = CheckpointCreate(
            name=name,
            modelBase=model_base,
            trainingMethod=training_method,
            trainingConfig=training_config,
            projectId=project_id,
            notes=notes,
        )
        response = self._client.post(
            "/checkpoints", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Checkpoint.model_validate(response.get("checkpoint"))

    def list(
        self,
        *,
        project_id: str | None = None,
        model_base: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Checkpoint]:
        """List all checkpoints with pagination.

        Args:
            project_id: Optional filter by project ID
            model_base: Optional filter by base model
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20, max: 100)

        Returns:
            Paginated list of checkpoints
        """
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if model_base:
            params["modelBase"] = model_base
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = self._client.get("/checkpoints", params=params or None)
        checkpoints = [Checkpoint.model_validate(c) for c in response.get("checkpoints", [])]
        return PaginatedResponse[Checkpoint](
            items=checkpoints,
            total=response.get("total", len(checkpoints)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(checkpoints)),
            hasMore=response.get("hasMore", False),
        )

    def get(self, checkpoint_id: str) -> Checkpoint:
        """Get a checkpoint by ID.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            The checkpoint
        """
        response = self._client.get(f"/checkpoints/{checkpoint_id}")
        return Checkpoint.model_validate(response.get("checkpoint"))

    def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/checkpoints/{checkpoint_id}")
        return True


class AsyncCheckpointsResource:
    """Async resource for model checkpoints."""

    def __init__(self, client: AsyncHTTPClient):
        self._client = client

    async def create(
        self,
        name: str,
        model_base: str,
        *,
        training_method: TrainingMethod | None = None,
        training_config: dict[str, Any] | None = None,
        project_id: str | None = None,
        notes: str | None = None,
    ) -> Checkpoint:
        """Register a new model checkpoint."""
        data = CheckpointCreate(
            name=name,
            modelBase=model_base,
            trainingMethod=training_method,
            trainingConfig=training_config,
            projectId=project_id,
            notes=notes,
        )
        response = await self._client.post(
            "/checkpoints", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Checkpoint.model_validate(response.get("checkpoint"))

    async def list(
        self,
        *,
        project_id: str | None = None,
        model_base: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Checkpoint]:
        """List all checkpoints with pagination."""
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if model_base:
            params["modelBase"] = model_base
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = await self._client.get("/checkpoints", params=params or None)
        checkpoints = [Checkpoint.model_validate(c) for c in response.get("checkpoints", [])]
        return PaginatedResponse[Checkpoint](
            items=checkpoints,
            total=response.get("total", len(checkpoints)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(checkpoints)),
            hasMore=response.get("hasMore", False),
        )

    async def get(self, checkpoint_id: str) -> Checkpoint:
        """Get a checkpoint by ID."""
        response = await self._client.get(f"/checkpoints/{checkpoint_id}")
        return Checkpoint.model_validate(response.get("checkpoint"))

    async def delete(self, checkpoint_id: str) -> bool:
        """Delete a checkpoint."""
        await self._client.delete(f"/checkpoints/{checkpoint_id}")
        return True
