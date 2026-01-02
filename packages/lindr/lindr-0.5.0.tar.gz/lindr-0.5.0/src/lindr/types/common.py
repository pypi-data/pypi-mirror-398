"""Common type definitions shared across resources."""

from __future__ import annotations

from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PersonalityDimensions(BaseModel):
    """10 personality dimensions (0-100 scale)."""

    model_config = ConfigDict(populate_by_name=True)

    openness: float = Field(ge=0, le=100)
    conscientiousness: float = Field(ge=0, le=100)
    extraversion: float = Field(ge=0, le=100)
    agreeableness: float = Field(ge=0, le=100)
    neuroticism: float = Field(ge=0, le=100)
    assertiveness: float = Field(ge=0, le=100)
    ambition: float = Field(ge=0, le=100)
    resilience: float = Field(ge=0, le=100)
    integrity: float = Field(ge=0, le=100)
    curiosity: float = Field(ge=0, le=100)


class Tolerances(BaseModel):
    """Per-dimension drift tolerances (0-100 scale)."""

    model_config = ConfigDict(populate_by_name=True)

    global_tolerance: float | None = Field(default=None, alias="global")
    openness: float | None = None
    conscientiousness: float | None = None
    extraversion: float | None = None
    agreeableness: float | None = None
    neuroticism: float | None = None
    assertiveness: float | None = None
    ambition: float | None = None
    resilience: float | None = None
    integrity: float | None = None
    curiosity: float | None = None


class Message(BaseModel):
    """A single message in a conversation."""

    role: str
    content: str


# Type aliases for literal types
EvalStatus = Literal["pending", "running", "completed", "failed"]
EvalContext = Literal["professional", "casual", "customer_support", "sales", "technical"]
TrainingMethod = Literal["lora", "full", "dpo", "rlhf", "other"]
Recommendation = Literal["ship", "review", "reject"]
DriftDirection = Literal["toward_target", "away_from_target", "neutral"]
ConfidenceLevel = Literal["high", "medium", "low"]


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated API response wrapper."""

    model_config = ConfigDict(populate_by_name=True)

    items: list[T]
    total: int
    page: int
    per_page: int = Field(alias="perPage")
    has_more: bool = Field(alias="hasMore")

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page
