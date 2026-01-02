"""Comparison type definitions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import DriftDirection, Recommendation


class DimensionDiff(BaseModel):
    """Per-dimension comparison data."""

    model_config = ConfigDict(populate_by_name=True)

    baseline_avg: float = Field(alias="baselineAvg")
    candidate_avg: float = Field(alias="candidateAvg")
    delta: float
    delta_percent: float = Field(alias="deltaPercent")
    direction: DriftDirection
    significant: bool


class ComparisonCreate(BaseModel):
    """Input for creating a comparison."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, max_length=100)
    baseline_eval_id: str = Field(alias="baselineEvalId")
    candidate_eval_id: str = Field(alias="candidateEvalId")
    project_id: str | None = Field(default=None, alias="projectId")


class Comparison(BaseModel):
    """A comparison between two eval runs."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str | None = None
    baseline_eval_id: str = Field(alias="baselineEvalId")
    candidate_eval_id: str = Field(alias="candidateEvalId")
    project_id: str | None = Field(default=None, alias="projectId")
    diff: dict[str, DimensionDiff] | None = None
    overall_improvement: float | None = Field(default=None, alias="overallImprovement")
    recommendation: Recommendation | None = None
    created_at: datetime = Field(alias="createdAt")
