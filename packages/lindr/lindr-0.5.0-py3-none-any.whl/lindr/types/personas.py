"""Persona type definitions."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .common import PersonalityDimensions, Tolerances


PersonaTemplateCategory = Literal[
    "customer_experience",
    "revenue_sales",
    "regulated_industries",
    "internal_operations",
]


class PersonaTemplateCategoryInfo(BaseModel):
    """Information about a persona template category."""

    label: str
    description: str


class PersonaTemplate(BaseModel):
    """A pre-built persona template for common enterprise use cases."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str
    category: PersonaTemplateCategory
    dimensions: PersonalityDimensions
    tolerances: Tolerances
    market_context: str | None = Field(default=None, alias="marketContext")


class PersonaCreate(BaseModel):
    """Input for creating a persona."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    project_id: str | None = Field(default=None, alias="projectId")
    dimensions: PersonalityDimensions
    tolerances: Tolerances | None = None
    is_default: bool = Field(default=False, alias="isDefault")


class PersonaUpdate(BaseModel):
    """Input for updating a persona."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    dimensions: PersonalityDimensions | None = None
    tolerances: Tolerances | None = None
    is_default: bool | None = Field(default=None, alias="isDefault")


class Persona(BaseModel):
    """A persona profile with target personality dimensions."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: str | None = None
    project_id: str | None = Field(default=None, alias="projectId")
    dimensions: PersonalityDimensions
    tolerances: Tolerances | None = None
    is_default: bool = Field(default=False, alias="isDefault")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


class PersonaTemplatesResponse(BaseModel):
    """Response containing persona templates."""

    model_config = ConfigDict(populate_by_name=True)

    templates: list[PersonaTemplate]
    categories: dict[str, PersonaTemplateCategoryInfo]
