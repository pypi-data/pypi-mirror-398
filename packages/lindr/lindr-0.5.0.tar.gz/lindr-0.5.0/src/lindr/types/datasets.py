"""Dataset type definitions."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .common import Message


class DatasetPrompt(BaseModel):
    """A single prompt in a dataset."""

    id: str
    messages: list[Message]
    category: str | None = None


class DatasetCreate(BaseModel):
    """Input for creating a dataset."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    project_id: str | None = Field(default=None, alias="projectId")
    prompts: list[DatasetPrompt] = Field(min_length=1, max_length=10000)


class Dataset(BaseModel):
    """A dataset of prompts for evaluation."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str | None = None
    project_id: str | None = Field(default=None, alias="projectId")
    prompt_count: int = Field(alias="promptCount")
    prompts: list[DatasetPrompt] | None = None
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
