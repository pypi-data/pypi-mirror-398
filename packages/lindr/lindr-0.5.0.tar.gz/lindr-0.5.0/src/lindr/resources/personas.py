"""Personas resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, overload

from ..types.common import PaginatedResponse, PersonalityDimensions, Tolerances
from ..types.personas import (
    Persona,
    PersonaCreate,
    PersonaTemplate,
    PersonaTemplateCategoryInfo,
    PersonaTemplateCategory,
    PersonaTemplatesResponse,
    PersonaUpdate,
)

if TYPE_CHECKING:
    from .._base import AsyncHTTPClient, SyncHTTPClient


class PersonasResource:
    """Sync resource for personas."""

    def __init__(self, client: SyncHTTPClient):
        self._client = client

    def create(
        self,
        name: str,
        dimensions: PersonalityDimensions,
        *,
        description: str | None = None,
        project_id: str | None = None,
        tolerances: Tolerances | None = None,
        is_default: bool = False,
    ) -> Persona:
        """Create a new persona.

        Args:
            name: Persona name
            dimensions: Target personality dimensions (0-100 scale)
            description: Optional description
            project_id: Optional project ID
            tolerances: Optional per-dimension tolerance thresholds
            is_default: Whether this is the default persona

        Returns:
            The created persona
        """
        data = PersonaCreate(
            name=name,
            dimensions=dimensions,
            description=description,
            projectId=project_id,
            tolerances=tolerances,
            isDefault=is_default,
        )
        response = self._client.post(
            "/personas", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Persona.model_validate(response.get("persona"))

    def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Persona]:
        """List all personas with pagination.

        Args:
            project_id: Optional filter by project ID
            page: Page number (1-indexed, default: 1)
            per_page: Items per page (default: 20, max: 100)

        Returns:
            Paginated list of personas
        """
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = self._client.get("/personas", params=params or None)
        personas = [Persona.model_validate(p) for p in response.get("personas", [])]
        return PaginatedResponse[Persona](
            items=personas,
            total=response.get("total", len(personas)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(personas)),
            hasMore=response.get("hasMore", False),
        )

    def get(self, persona_id: str) -> Persona:
        """Get a persona by ID.

        Args:
            persona_id: Persona ID

        Returns:
            The persona
        """
        response = self._client.get(f"/personas/{persona_id}")
        return Persona.model_validate(response.get("persona"))

    def update(
        self,
        persona_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        dimensions: PersonalityDimensions | None = None,
        tolerances: Tolerances | None = None,
        is_default: bool | None = None,
    ) -> Persona:
        """Update a persona.

        Args:
            persona_id: Persona ID
            name: New name
            description: New description
            dimensions: New target dimensions
            tolerances: New tolerances
            is_default: Whether this is the default persona

        Returns:
            The updated persona
        """
        data = PersonaUpdate(
            name=name,
            description=description,
            dimensions=dimensions,
            tolerances=tolerances,
            isDefault=is_default,
        )
        response = self._client.patch(
            f"/personas/{persona_id}",
            json=data.model_dump(by_alias=True, exclude_none=True),
        )
        return Persona.model_validate(response.get("persona"))

    def delete(self, persona_id: str) -> bool:
        """Delete a persona.

        Args:
            persona_id: Persona ID

        Returns:
            True if deleted successfully
        """
        self._client.delete(f"/personas/{persona_id}")
        return True

    def list_templates(
        self,
        *,
        category: PersonaTemplateCategory | None = None,
    ) -> list[PersonaTemplate]:
        """List available persona templates.

        Pre-built templates for common enterprise use cases including
        customer support, sales, healthcare, financial services, and more.

        Args:
            category: Optional filter by category:
                - customer_experience: Support, escalation, e-commerce
                - revenue_sales: SDR, retention, collections
                - regulated_industries: Healthcare, finance, insurance, legal
                - internal_operations: HR, IT helpdesk, code review

        Returns:
            List of persona templates
        """
        params: dict[str, str] = {}
        if category:
            params["category"] = category
        response = self._client.get("/personas/templates", params=params or None)
        return [
            PersonaTemplate.model_validate(t) for t in response.get("templates", [])
        ]

    def get_template(self, template_id: str) -> PersonaTemplate | None:
        """Get a specific persona template by ID.

        Args:
            template_id: Template ID (e.g., 'tier-1-support-agent')

        Returns:
            The template if found, None otherwise
        """
        templates = self.list_templates()
        return next((t for t in templates if t.id == template_id), None)

    def create_from_template(
        self,
        template_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        project_id: str | None = None,
        is_default: bool = False,
    ) -> Persona:
        """Create a persona from a template.

        Args:
            template_id: Template ID (e.g., 'tier-1-support-agent')
            name: Override the template name
            description: Override the template description
            project_id: Optional project ID
            is_default: Whether this is the default persona

        Returns:
            The created persona

        Raises:
            ValueError: If template not found
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return self.create(
            name=name or template.name,
            dimensions=template.dimensions,
            description=description or template.description,
            project_id=project_id,
            tolerances=template.tolerances,
            is_default=is_default,
        )


class AsyncPersonasResource:
    """Async resource for personas."""

    def __init__(self, client: AsyncHTTPClient):
        self._client = client

    async def create(
        self,
        name: str,
        dimensions: PersonalityDimensions,
        *,
        description: str | None = None,
        project_id: str | None = None,
        tolerances: Tolerances | None = None,
        is_default: bool = False,
    ) -> Persona:
        """Create a new persona."""
        data = PersonaCreate(
            name=name,
            dimensions=dimensions,
            description=description,
            projectId=project_id,
            tolerances=tolerances,
            isDefault=is_default,
        )
        response = await self._client.post(
            "/personas", json=data.model_dump(by_alias=True, exclude_none=True)
        )
        return Persona.model_validate(response.get("persona"))

    async def list(
        self,
        *,
        project_id: str | None = None,
        page: int | None = None,
        per_page: int | None = None,
    ) -> PaginatedResponse[Persona]:
        """List all personas with pagination."""
        params: dict[str, str] = {}
        if project_id:
            params["projectId"] = project_id
        if page is not None:
            params["page"] = str(page)
        if per_page is not None:
            params["perPage"] = str(per_page)
        response = await self._client.get("/personas", params=params or None)
        personas = [Persona.model_validate(p) for p in response.get("personas", [])]
        return PaginatedResponse[Persona](
            items=personas,
            total=response.get("total", len(personas)),
            page=response.get("page", 1),
            perPage=response.get("perPage", len(personas)),
            hasMore=response.get("hasMore", False),
        )

    async def get(self, persona_id: str) -> Persona:
        """Get a persona by ID."""
        response = await self._client.get(f"/personas/{persona_id}")
        return Persona.model_validate(response.get("persona"))

    async def update(
        self,
        persona_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        dimensions: PersonalityDimensions | None = None,
        tolerances: Tolerances | None = None,
        is_default: bool | None = None,
    ) -> Persona:
        """Update a persona."""
        data = PersonaUpdate(
            name=name,
            description=description,
            dimensions=dimensions,
            tolerances=tolerances,
            isDefault=is_default,
        )
        response = await self._client.patch(
            f"/personas/{persona_id}",
            json=data.model_dump(by_alias=True, exclude_none=True),
        )
        return Persona.model_validate(response.get("persona"))

    async def delete(self, persona_id: str) -> bool:
        """Delete a persona."""
        await self._client.delete(f"/personas/{persona_id}")
        return True

    async def list_templates(
        self,
        *,
        category: PersonaTemplateCategory | None = None,
    ) -> list[PersonaTemplate]:
        """List available persona templates.

        Pre-built templates for common enterprise use cases including
        customer support, sales, healthcare, financial services, and more.

        Args:
            category: Optional filter by category:
                - customer_experience: Support, escalation, e-commerce
                - revenue_sales: SDR, retention, collections
                - regulated_industries: Healthcare, finance, insurance, legal
                - internal_operations: HR, IT helpdesk, code review

        Returns:
            List of persona templates
        """
        params: dict[str, str] = {}
        if category:
            params["category"] = category
        response = await self._client.get("/personas/templates", params=params or None)
        return [
            PersonaTemplate.model_validate(t) for t in response.get("templates", [])
        ]

    async def get_template(self, template_id: str) -> PersonaTemplate | None:
        """Get a specific persona template by ID.

        Args:
            template_id: Template ID (e.g., 'tier-1-support-agent')

        Returns:
            The template if found, None otherwise
        """
        templates = await self.list_templates()
        return next((t for t in templates if t.id == template_id), None)

    async def create_from_template(
        self,
        template_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        project_id: str | None = None,
        is_default: bool = False,
    ) -> Persona:
        """Create a persona from a template.

        Args:
            template_id: Template ID (e.g., 'tier-1-support-agent')
            name: Override the template name
            description: Override the template description
            project_id: Optional project ID
            is_default: Whether this is the default persona

        Returns:
            The created persona

        Raises:
            ValueError: If template not found
        """
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return await self.create(
            name=name or template.name,
            dimensions=template.dimensions,
            description=description or template.description,
            project_id=project_id,
            tolerances=template.tolerances,
            is_default=is_default,
        )
