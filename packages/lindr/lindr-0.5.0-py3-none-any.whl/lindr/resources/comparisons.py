"""Comparisons resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..types.common import PaginatedResponse
from ..types.comparisons import Comparison, ComparisonCreate

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class ComparisonsResource:
    """Sync resource for comparisons."""

    def __init__(self, client: SyncHTTPClient):
        self._client = client

    def create(
        self,
        baseline_eval_id: str,
        candidate_eval_id: str,
        *,
        name: str | None = None,
        project_id: str | None = None,
    ) -> Comparison:
        """Create a comparison between two eval runs.

        Both eval runs must reference the same persona.

        Args:
            baseline_eval_id: Baseline eval run ID
            candidate_eval_id: Candidate (fine-tuned) eval run ID
            name: Optional comparison name
            project_id: Optional project ID

        Returns:
            The comparison with diff and recommendation
        """
        data = ComparisonCreate(
            baselineEvalId=baseline_eval_id,
            candidateEvalId=candidate_eval_id,
            name=name,
            projectId=project_id,
        )
        response = self._client.post(
            "/comparisons", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Comparison.model_validate(response.get("comparison"))

    def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Comparison]:
        """List all comparisons with pagination.

        Args:
            project_id: Optional filter by project ID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20, max: 100)

        Returns:
            Paginated list of comparisons
        """
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = self._client.get("/comparisons", params=params or None)
        comparisons = [Comparison.model_validate(c) for c in response.get("comparisons", [])]
        return PaginatedResponse[Comparison](
            items=comparisons,
            total=response.get("total", len(comparisons)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(comparisons)),
            hasMore=response.get("hasMore", False),
        )

    def get(self, comparison_id: str) -> Comparison:
        """Get a comparison by ID.

        Args:
            comparison_id: Comparison ID

        Returns:
            The comparison with full details
        """
        response = self._client.get(f"/comparisons/{comparison_id}")
        return Comparison.model_validate(response.get("comparison"))

    def delete(self, comparison_id: str) -> bool:
        """Delete a comparison.

        Args:
            comparison_id: Comparison ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/comparisons/{comparison_id}")
        return True


class AsyncComparisonsResource:
    """Async resource for comparisons."""

    def __init__(self, client: AsyncHTTPClient):
        self._client = client

    async def create(
        self,
        baseline_eval_id: str,
        candidate_eval_id: str,
        *,
        name: str | None = None,
        project_id: str | None = None,
    ) -> Comparison:
        """Create a comparison between two eval runs."""
        data = ComparisonCreate(
            baselineEvalId=baseline_eval_id,
            candidateEvalId=candidate_eval_id,
            name=name,
            projectId=project_id,
        )
        response = await self._client.post(
            "/comparisons", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Comparison.model_validate(response.get("comparison"))

    async def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Comparison]:
        """List all comparisons with pagination."""
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = await self._client.get("/comparisons", params=params or None)
        comparisons = [Comparison.model_validate(c) for c in response.get("comparisons", [])]
        return PaginatedResponse[Comparison](
            items=comparisons,
            total=response.get("total", len(comparisons)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(comparisons)),
            hasMore=response.get("hasMore", False),
        )

    async def get(self, comparison_id: str) -> Comparison:
        """Get a comparison by ID."""
        response = await self._client.get(f"/comparisons/{comparison_id}")
        return Comparison.model_validate(response.get("comparison"))

    async def delete(self, comparison_id: str) -> bool:
        """Delete a comparison."""
        await self._client.delete(f"/comparisons/{comparison_id}")
        return True
