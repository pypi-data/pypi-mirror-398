"""Eval type definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .common import EvalContext, EvalStatus, Message, PersonalityDimensions


class EvalSample(BaseModel):
    """A single sample for batch evaluation."""

    id: str
    content: str
    messages: list[Message] | None = None
    metadata: dict[str, Any] | None = None


class EvalRunCreate(BaseModel):
    """Input for creating an eval run."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    persona_id: str = Field(alias="personaId")
    dataset_id: str | None = Field(default=None, alias="datasetId")
    checkpoint_id: str | None = Field(default=None, alias="checkpointId")
    project_id: str | None = Field(default=None, alias="projectId")
    model_name: str | None = Field(default=None, alias="modelName")


class BatchEvalCreate(BaseModel):
    """Input for batch evaluation."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    persona_id: str = Field(alias="personaId")
    context: EvalContext = Field(description="Context for baseline normalization")
    dataset_id: str | None = Field(default=None, alias="datasetId")
    checkpoint_id: str | None = Field(default=None, alias="checkpointId")
    project_id: str | None = Field(default=None, alias="projectId")
    model_name: str | None = Field(default=None, alias="modelName")
    monitor_id: str | None = Field(default=None, alias="monitorId")
    samples: list[EvalSample] | None = None
    options: dict[str, Any] | None = None


class EvalRun(BaseModel):
    """An evaluation run."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    persona_id: str = Field(alias="personaId")
    dataset_id: str | None = Field(default=None, alias="datasetId")
    checkpoint_id: str | None = Field(default=None, alias="checkpointId")
    project_id: str | None = Field(default=None, alias="projectId")
    name: str
    status: EvalStatus
    context: EvalContext | None = Field(default=None, description="Context used for baseline normalization")
    model_name: str | None = Field(default=None, alias="modelName")
    sample_count: int | None = Field(default=None, alias="sampleCount")
    avg_scores: PersonalityDimensions | None = Field(default=None, alias="avgScores")
    avg_drift: float | None = Field(default=None, alias="avgDrift")
    flagged_count: int | None = Field(default=None, alias="flaggedCount")
    error_message: str | None = Field(default=None, alias="errorMessage")
    completed_at: datetime | None = Field(default=None, alias="completedAt")
    created_at: datetime = Field(alias="createdAt")


class EvalResult(BaseModel):
    """A single evaluation result."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    eval_run_id: str = Field(alias="evalRunId")
    sample_id: str = Field(alias="sampleId")
    input_prompt: dict[str, Any] | None = Field(default=None, alias="inputPrompt")
    response_content: str | None = Field(default=None, alias="responseContent")
    scores: PersonalityDimensions | None = None
    confidence: dict[str, str] | None = None
    overall_confidence: str | None = Field(default=None, alias="overallConfidence")
    drift: float | None = None
    drift_details: dict[str, float] | None = Field(default=None, alias="driftDetails")
    flagged: bool = False
    flag_reason: str | None = Field(default=None, alias="flagReason")
    created_at: datetime = Field(alias="createdAt")


class BatchEvalSummary(BaseModel):
    """Summary statistics from batch evaluation."""

    model_config = ConfigDict(populate_by_name=True)

    sample_count: int = Field(alias="sampleCount")
    success_count: int = Field(alias="successCount")
    error_count: int = Field(alias="errorCount")
    avg_scores: PersonalityDimensions = Field(alias="avgScores")
    avg_drift: float = Field(alias="avgDrift")
    flagged_count: int = Field(alias="flaggedCount")
