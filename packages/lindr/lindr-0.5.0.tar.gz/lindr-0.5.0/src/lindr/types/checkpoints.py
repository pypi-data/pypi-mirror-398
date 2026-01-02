"""Checkpoint type definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .common import TrainingMethod


class CheckpointCreate(BaseModel):
    """Input for creating a model checkpoint."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    model_base: str = Field(min_length=1, max_length=100, alias="modelBase")
    training_method: TrainingMethod | None = Field(default=None, alias="trainingMethod")
    training_config: dict[str, Any] | None = Field(default=None, alias="trainingConfig")
    project_id: str | None = Field(default=None, alias="projectId")
    notes: str | None = Field(default=None, max_length=1000)


class Checkpoint(BaseModel):
    """A model checkpoint for tracking fine-tune versions."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    model_base: str = Field(alias="modelBase")
    training_method: TrainingMethod | None = Field(default=None, alias="trainingMethod")
    training_config: dict[str, Any] | None = Field(default=None, alias="trainingConfig")
    project_id: str | None = Field(default=None, alias="projectId")
    notes: str | None = None
    created_at: datetime = Field(alias="createdAt")
