"""Evals resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..types.common import PaginatedResponse
from ..types.common import EvalContext
from ..types.evals import (
    BatchEvalCreate,
    BatchEvalSummary,
    EvalResult,
    EvalRun,
    EvalRunCreate,
    EvalSample,
)

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class EvalsResource:
    """Sync resource for evaluations."""

    def __init__(self, client: SyncHTTPClient):
        self._client = client

    def create(
        self,
        name: str,
        persona_id: str,
        *,
        dataset_id: str | None = None,
        checkpoint_id: str | None = None,
        project_id: str | None = None,
        model_name: str | None = None,
    ) -> EvalRun:
        """Create an eval run without executing it.

        Args:
            name: Eval run name
            persona_id: Persona ID to evaluate against
            dataset_id: Optional dataset ID
            checkpoint_id: Optional model checkpoint ID
            project_id: Optional project ID
            model_name: Optional model name

        Returns:
            The created eval run (status: pending)
        """
        data = EvalRunCreate(
            name=name,
            personaId=persona_id,
            datasetId=dataset_id,
            checkpointId=checkpoint_id,
            projectId=project_id,
            modelName=model_name,
        )
        response = self._client.post(
            "/evals", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return EvalRun.model_validate(response.get("evalRun"))

    def batch(
        self,
        name: str,
        persona_id: str,
        context: EvalContext,
        *,
        dataset_id: str | None = None,
        samples: list[dict[str, Any]] | None = None,
        checkpoint_id: str | None = None,
        project_id: str | None = None,
        model_name: str | None = None,
        monitor_id: str | None = None,
        concurrency: int | None = None,
    ) -> tuple[EvalRun, BatchEvalSummary]:
        """Run a batch evaluation with context-aware normalization.

        Either dataset_id or samples must be provided.

        Args:
            name: Eval run name
            persona_id: Persona ID to evaluate against
            context: Context for baseline normalization (professional, casual,
                customer_support, sales, technical)
            dataset_id: Dataset ID to use for samples
            samples: List of samples with id and content
            checkpoint_id: Optional model checkpoint ID
            project_id: Optional project ID
            model_name: Optional model name
            monitor_id: Optional monitor ID for running dataset prompts
            concurrency: Number of samples to process in parallel (1-50)

        Returns:
            Tuple of (eval_run, summary)
        """
        sample_models = [EvalSample.model_validate(s) for s in samples] if samples else None
        options = {"concurrency": concurrency} if concurrency else None

        data = BatchEvalCreate(
            name=name,
            personaId=persona_id,
            context=context,
            datasetId=dataset_id,
            samples=sample_models,
            checkpointId=checkpoint_id,
            projectId=project_id,
            modelName=model_name,
            monitorId=monitor_id,
            options=options,
        )
        response = self._client.post(
            "/evals/batch", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        eval_run = EvalRun.model_validate(response.get("evalRun"))
        summary = BatchEvalSummary.model_validate(response.get("summary"))
        return eval_run, summary

    def list(
        self,
        *,
        project_id: str | None = None,
        persona_id: str | None = None,
        status: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[EvalRun]:
        """List eval runs with pagination.

        Args:
            project_id: Optional filter by project ID
            persona_id: Optional filter by persona ID
            status: Optional filter by status
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20, max: 100)

        Returns:
            Paginated list of eval runs
        """
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if persona_id:
            params["personaId"] = persona_id
        if status:
            params["status"] = status
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = self._client.get("/evals", params=params or None)
        eval_runs = [EvalRun.model_validate(e) for e in response.get("evalRuns", [])]
        return PaginatedResponse[EvalRun](
            items=eval_runs,
            total=response.get("total", len(eval_runs)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(eval_runs)),
            hasMore=response.get("hasMore", False),
        )

    def get(
        self, eval_id: str, *, include_results: bool = True
    ) -> tuple[EvalRun, list[EvalResult] | None]:
        """Get an eval run with optional results.

        Args:
            eval_id: Eval run ID
            include_results: Whether to include individual results

        Returns:
            Tuple of (eval_run, results or None)
        """
        params = {"includeResults": "true" if include_results else "false"}
        response = self._client.get(f"/evals/{eval_id}", params=params)
        eval_run = EvalRun.model_validate(response.get("evalRun"))
        results = None
        if include_results and response.get("results"):
            results = [EvalResult.model_validate(r) for r in response.get("results", [])]
        return eval_run, results

    def delete(self, eval_id: str) -> bool:
        """Delete an eval run and its results.

        Args:
            eval_id: Eval run ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/evals/{eval_id}")
        return True


class AsyncEvalsResource:
    """Async resource for evaluations."""

    def __init__(self, client: AsyncHTTPClient):
        self._client = client

    async def create(
        self,
        name: str,
        persona_id: str,
        *,
        dataset_id: str | None = None,
        checkpoint_id: str | None = None,
        project_id: str | None = None,
        model_name: str | None = None,
    ) -> EvalRun:
        """Create an eval run without executing it."""
        data = EvalRunCreate(
            name=name,
            personaId=persona_id,
            datasetId=dataset_id,
            checkpointId=checkpoint_id,
            projectId=project_id,
            modelName=model_name,
        )
        response = await self._client.post(
            "/evals", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return EvalRun.model_validate(response.get("evalRun"))

    async def batch(
        self,
        name: str,
        persona_id: str,
        context: EvalContext,
        *,
        dataset_id: str | None = None,
        samples: list[dict[str, Any]] | None = None,
        checkpoint_id: str | None = None,
        project_id: str | None = None,
        model_name: str | None = None,
        monitor_id: str | None = None,
        concurrency: int | None = None,
    ) -> tuple[EvalRun, BatchEvalSummary]:
        """Run a batch evaluation with context-aware normalization."""
        sample_models = [EvalSample.model_validate(s) for s in samples] if samples else None
        options = {"concurrency": concurrency} if concurrency else None

        data = BatchEvalCreate(
            name=name,
            personaId=persona_id,
            context=context,
            datasetId=dataset_id,
            samples=sample_models,
            checkpointId=checkpoint_id,
            projectId=project_id,
            modelName=model_name,
            monitorId=monitor_id,
            options=options,
        )
        response = await self._client.post(
            "/evals/batch", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        eval_run = EvalRun.model_validate(response.get("evalRun"))
        summary = BatchEvalSummary.model_validate(response.get("summary"))
        return eval_run, summary

    async def list(
        self,
        *,
        project_id: str | None = None,
        persona_id: str | None = None,
        status: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[EvalRun]:
        """List eval runs with pagination."""
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if persona_id:
            params["personaId"] = persona_id
        if status:
            params["status"] = status
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = await self._client.get("/evals", params=params or None)
        eval_runs = [EvalRun.model_validate(e) for e in response.get("evalRuns", [])]
        return PaginatedResponse[EvalRun](
            items=eval_runs,
            total=response.get("total", len(eval_runs)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(eval_runs)),
            hasMore=response.get("hasMore", False),
        )

    async def get(
        self, eval_id: str, *, include_results: bool = True
    ) -> tuple[EvalRun, list[EvalResult] | None]:
        """Get an eval run with optional results."""
        params = {"includeResults": "true" if include_results else "false"}
        response = await self._client.get(f"/evals/{eval_id}", params=params)
        eval_run = EvalRun.model_validate(response.get("evalRun"))
        results = None
        if include_results and response.get("results"):
            results = [EvalResult.model_validate(r) for r in response.get("results", [])]
        return eval_run, results

    async def delete(self, eval_id: str) -> bool:
        """Delete an eval run and its results."""
        await self._client.delete(f"/evals/{eval_id}")
        return True
