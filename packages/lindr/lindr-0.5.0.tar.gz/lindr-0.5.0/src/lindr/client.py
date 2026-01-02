"""Lindr API clients."""

from __future__ import annotations

from ._base import AsyncHTTPClient, SyncHTTPClient
from .resources.checkpoints import AsyncCheckpointsResource, CheckpointsResource
from .resources.comparisons import AsyncComparisonsResource, ComparisonsResource
from .resources.datasets import AsyncDatasetsResource, DatasetsResource
from .resources.evals import AsyncEvalsResource, EvalsResource
from .resources.personas import AsyncPersonasResource, PersonasResource


class Client:
    """Synchronous Lindr API client.

    Usage:
        ```python
        import lindr

        client = lindr.Client(api_key="lnd_...")

        # Create a persona
        persona = client.personas.create(
            name="Support Agent",
            dimensions=lindr.PersonalityDimensions(
                openness=70,
                conscientiousness=85,
                extraversion=60,
                agreeableness=90,
                neuroticism=20,
                assertiveness=65,
                ambition=70,
                resilience=80,
                integrity=95,
                curiosity=75,
            ),
        )

        # Create a dataset
        dataset = client.datasets.create(
            name="My Dataset",
            prompts=[{"id": "1", "messages": [...]}]
        )

        # Run batch evaluation
        eval_run, summary = client.evals.batch(
            name="v1 Eval",
            persona_id=persona.id,
            dataset_id=dataset.id
        )

        # Compare with another eval
        comparison = client.comparisons.create(
            baseline_eval_id=baseline.id,
            candidate_eval_id=candidate.id
        )
        print(comparison.recommendation)  # "ship", "review", or "reject"
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the Lindr client.

        Args:
            api_key: API key. Falls back to LINDR_API_KEY env var.
            base_url: Override API base URL. Falls back to LINDR_BASE_URL env var.
            timeout: Request timeout in seconds (default: 30)
        """
        self._client = SyncHTTPClient(api_key=api_key, base_url=base_url, timeout=timeout)
        self.datasets = DatasetsResource(self._client)
        self.personas = PersonasResource(self._client)
        self.evals = EvalsResource(self._client)
        self.comparisons = ComparisonsResource(self._client)
        self.checkpoints = CheckpointsResource(self._client)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncClient:
    """Asynchronous Lindr API client.

    Usage:
        ```python
        import asyncio
        import lindr

        async def main():
            async with lindr.AsyncClient(api_key="lnd_...") as client:
                # Run multiple evals in parallel
                tasks = [
                    client.evals.batch(
                        name=f"Eval {i}",
                        persona_id=persona_id,
                        samples=samples,
                    )
                    for i in range(5)
                ]
                results = await asyncio.gather(*tasks)

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the async Lindr client.

        Args:
            api_key: API key. Falls back to LINDR_API_KEY env var.
            base_url: Override API base URL. Falls back to LINDR_BASE_URL env var.
            timeout: Request timeout in seconds (default: 30)
        """
        self._client = AsyncHTTPClient(api_key=api_key, base_url=base_url, timeout=timeout)
        self.datasets = AsyncDatasetsResource(self._client)
        self.personas = AsyncPersonasResource(self._client)
        self.evals = AsyncEvalsResource(self._client)
        self.comparisons = AsyncComparisonsResource(self._client)
        self.checkpoints = AsyncCheckpointsResource(self._client)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.close()

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
