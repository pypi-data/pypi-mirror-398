"""Training data resource for exporting classifier training data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class TrainingDataResource:
    """Sync resource for exporting training data."""

    def __init__(self, client: "SyncHTTPClient"):
        self._client = client

    def export(
        self,
        *,
        output_path: str | Path | None = None,
        min_confidence: Literal["low", "medium", "high"] = "medium",
        persona_ids: list[str] | None = None,
        project_id: str | None = None,
        include_embeddings: bool = True,
        format: Literal["json", "jsonl"] = "json",
        limit: int = 10000,
    ) -> dict | Path:
        """Export training data for classifier training.

        Args:
            output_path: If provided, save to file and return path
            min_confidence: Minimum confidence level for samples
            persona_ids: Filter by specific persona IDs
            project_id: Filter by project ID
            include_embeddings: Include pre-computed embeddings
            format: Output format (json or jsonl)
            limit: Maximum number of samples to export

        Returns:
            Dict with export data if no output_path, otherwise the Path
        """
        params: dict[str, str] = {
            "minConfidence": min_confidence,
            "includeEmbeddings": str(include_embeddings).lower(),
            "format": format,
            "limit": str(limit),
        }

        if persona_ids:
            params["personaIds"] = ",".join(persona_ids)
        if project_id:
            params["projectId"] = project_id

        response = self._client.get("/training-data/export", params=params)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                if format == "jsonl":
                    for sample in response.get("samples", []):
                        f.write(json.dumps(sample) + "\n")
                else:
                    json.dump(response, f, indent=2)

            return output_path

        return response


class AsyncTrainingDataResource:
    """Async resource for exporting training data."""

    def __init__(self, client: "AsyncHTTPClient"):
        self._client = client

    async def export(
        self,
        *,
        output_path: str | Path | None = None,
        min_confidence: Literal["low", "medium", "high"] = "medium",
        persona_ids: list[str] | None = None,
        project_id: str | None = None,
        include_embeddings: bool = True,
        format: Literal["json", "jsonl"] = "json",
        limit: int = 10000,
    ) -> dict | Path:
        """Export training data for classifier training.

        Args:
            output_path: If provided, save to file and return path
            min_confidence: Minimum confidence level for samples
            persona_ids: Filter by specific persona IDs
            project_id: Filter by project ID
            include_embeddings: Include pre-computed embeddings
            format: Output format (json or jsonl)
            limit: Maximum number of samples to export

        Returns:
            Dict with export data if no output_path, otherwise the Path
        """
        params: dict[str, str] = {
            "minConfidence": min_confidence,
            "includeEmbeddings": str(include_embeddings).lower(),
            "format": format,
            "limit": str(limit),
        }

        if persona_ids:
            params["personaIds"] = ",".join(persona_ids)
        if project_id:
            params["projectId"] = project_id

        response = await self._client.get("/training-data/export", params=params)

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "w", encoding="utf-8") as f:
                if format == "jsonl":
                    for sample in response.get("samples", []):
                        f.write(json.dumps(sample) + "\n")
                else:
                    json.dump(response, f, indent=2)

            return output_path

        return response
