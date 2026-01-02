"""Lindr Python SDK - LLM Personality Evaluation API.

Lindr helps you validate fine-tuned models by measuring behavioral personality
across 10 dimensions. Compare base vs. fine-tuned models and catch personality
drift before deploying to production.

Quick start with templates:
    ```python
    import lindr

    client = lindr.Client(api_key="lnd_...")

    # List available persona templates
    templates = client.personas.list_templates()
    # Categories: customer_experience, revenue_sales, regulated_industries, internal_operations

    # Create a persona from a template
    persona = client.personas.create_from_template(
        "tier-1-support-agent",
        name="My Support Bot",
    )

    # Run batch evaluation
    eval_run, summary = client.evals.batch(
        name="Baseline v1",
        persona_id=persona.id,
        samples=[
            {"id": "1", "content": "Response from model..."},
        ],
    )

    print(f"Avg drift: {summary.avg_drift:.1f}%")
    ```

Available templates:
    - tier-1-support-agent: High-volume frontline support
    - technical-support-specialist: L2/L3 troubleshooting
    - escalation-complaints-handler: De-escalation specialist
    - ecommerce-shopping-assistant: Product recommendations
    - sales-development-rep: Outbound prospecting (SDR)
    - retention-renewals-specialist: Customer retention
    - collections-ar-agent: Payment collection
    - healthcare-patient-communicator: HIPAA-aware patient triage
    - financial-services-advisor: Compliance-aware guidance
    - insurance-claims-processor: Claims intake and status
    - legal-compliance-reviewer: Contract review and risk
    - hr-people-operations: Employee support
    - it-helpdesk-agent: Internal tech support
    - code-review-assistant: PR feedback and standards
"""

from ._exceptions import (
    APIError,
    AuthenticationError,
    ConnectionError,
    LindrError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ._version import __version__
from .client import AsyncClient, Client
from .types.checkpoints import Checkpoint, CheckpointCreate
from .types.common import (
    DriftDirection,
    EvalStatus,
    Message,
    PaginatedResponse,
    PersonalityDimensions,
    Recommendation,
    Tolerances,
    TrainingMethod,
)
from .types.comparisons import Comparison, ComparisonCreate, DimensionDiff
from .types.datasets import Dataset, DatasetCreate, DatasetPrompt
from .types.evals import BatchEvalSummary, EvalResult, EvalRun, EvalRunCreate, EvalSample
from .types.personas import (
    Persona,
    PersonaCreate,
    PersonaTemplate,
    PersonaTemplateCategory,
    PersonaTemplateCategoryInfo,
)

__all__ = [
    # Version
    "__version__",
    # Clients
    "Client",
    "AsyncClient",
    # Exceptions
    "LindrError",
    "AuthenticationError",
    "ConnectionError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "APIError",
    # Common types
    "PersonalityDimensions",
    "Tolerances",
    "Message",
    "EvalStatus",
    "TrainingMethod",
    "Recommendation",
    "DriftDirection",
    "PaginatedResponse",
    # Datasets
    "Dataset",
    "DatasetCreate",
    "DatasetPrompt",
    # Personas
    "Persona",
    "PersonaCreate",
    "PersonaTemplate",
    "PersonaTemplateCategory",
    "PersonaTemplateCategoryInfo",
    # Evals
    "EvalRun",
    "EvalRunCreate",
    "EvalResult",
    "EvalSample",
    "BatchEvalSummary",
    # Comparisons
    "Comparison",
    "ComparisonCreate",
    "DimensionDiff",
    # Checkpoints
    "Checkpoint",
    "CheckpointCreate",
]
