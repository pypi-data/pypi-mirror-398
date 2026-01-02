# Lindr Python SDK

Python SDK for the [Lindr](https://lindr.io) LLM personality evaluation API.

Lindr helps you validate fine-tuned models by measuring behavioral personality across 10 dimensions. Compare base vs. fine-tuned models and catch personality drift before deploying to production.

## Installation

```bash
pip install lindr
```

## Quick Start

```python
import lindr

# Initialize client
client = lindr.Client(api_key="lnd_...")

# Create a persona (your target personality profile)
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

# Run baseline evaluation
samples = [
    {"id": "1", "content": "Response from base model..."},
    {"id": "2", "content": "Another response..."},
]

baseline, summary = client.evals.batch(
    name="llama-3.2-8b Baseline",
    persona_id=persona.id,
    samples=samples,
)
print(f"Avg drift: {summary.avg_drift:.1f}%")

# After fine-tuning, evaluate again
candidate, _ = client.evals.batch(
    name="llama-3.2-8b-dpo-v1",
    persona_id=persona.id,
    samples=finetuned_samples,
)

# Compare results
comparison = client.comparisons.create(
    baseline_eval_id=baseline.id,
    candidate_eval_id=candidate.id,
)
print(f"Recommendation: {comparison.recommendation}")  # "ship", "review", or "reject"
```

## Features

- **Batch Evaluations**: Analyze multiple LLM responses in parallel
- **10 Personality Dimensions**: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism, Assertiveness, Ambition, Resilience, Integrity, Curiosity
- **A/B Comparisons**: Compare baseline vs. fine-tuned models
- **Ship/Review/Reject Recommendations**: Get actionable guidance on model quality
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Pagination**: Efficiently iterate through large result sets
- **Async Support**: Full async/await support for high-throughput applications

## Pagination

All list methods return paginated responses:

```python
# Get first page
result = client.personas.list(page=1, per_page=10)

print(f"Total personas: {result.total}")
print(f"Page {result.page} of {result.total_pages}")
print(f"Has more: {result.has_more}")

# Iterate through all personas
for persona in result.items:
    print(f"- {persona.name}")

# Get next page
if result.has_more:
    next_page = client.personas.list(page=2, per_page=10)
```

## Model Checkpoints

Track fine-tuning iterations with checkpoints:

```python
# Register a checkpoint
checkpoint = client.checkpoints.create(
    name="llama-3.2-8b-dpo-v1",
    model_base="llama-3.2-8b",
    training_method="dpo",
    notes="First DPO fine-tune with safety data",
)

# Run eval with checkpoint tracking
eval_run, summary = client.evals.batch(
    name="DPO v1 Eval",
    persona_id=persona.id,
    checkpoint_id=checkpoint.id,
    samples=samples,
)
```

## Datasets

Create reusable prompt datasets:

```python
# Create a dataset
dataset = client.datasets.create(
    name="Support Scenarios",
    prompts=[
        {
            "id": "greeting",
            "messages": [{"role": "user", "content": "Hello, I need help"}],
            "category": "greeting",
        },
        {
            "id": "complaint",
            "messages": [{"role": "user", "content": "This is unacceptable!"}],
            "category": "complaint",
        },
    ],
)

# Run eval with dataset (requires monitor for generation)
eval_run, summary = client.evals.batch(
    name="Dataset Eval",
    persona_id=persona.id,
    dataset_id=dataset.id,
    monitor_id="mon_xxx",  # Monitor to generate responses
)
```

## Error Handling

The SDK provides typed exceptions for common error cases:

```python
import lindr

try:
    persona = client.personas.get("invalid_id")
except lindr.NotFoundError:
    print("Persona not found")
except lindr.RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except lindr.ValidationError as e:
    print(f"Validation failed: {e.details}")
except lindr.AuthenticationError:
    print("Invalid API key")
except lindr.APIError as e:
    print(f"API error ({e.status_code}): {e}")
```

### Automatic Retries

The SDK automatically retries failed requests with exponential backoff:

```python
# Default: 3 retries with exponential backoff
client = lindr.Client(api_key="lnd_...")

# Customize retry behavior
client = lindr.Client(
    api_key="lnd_...",
    max_retries=5,  # More retries for unreliable networks
)

# Disable retries
client = lindr.Client(
    api_key="lnd_...",
    max_retries=0,
)
```

Retried status codes: `429` (rate limit), `500`, `502`, `503`, `504`

## Async Usage

```python
import asyncio
import lindr

async def main():
    async with lindr.AsyncClient(api_key="lnd_...") as client:
        # List with pagination
        result = await client.personas.list()

        # Run multiple evals in parallel
        tasks = [
            client.evals.batch(
                name=f"Eval {i}",
                persona_id=persona_id,
                samples=sample_batches[i],
            )
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)

asyncio.run(main())
```

## Configuration

### Environment Variables

- `LINDR_API_KEY`: Your API key (alternative to passing `api_key` to client)
- `LINDR_BASE_URL`: Override API base URL (default: `https://api.lindr.io/api/v1`)

### Client Options

```python
client = lindr.Client(
    api_key="lnd_...",           # Required (or use LINDR_API_KEY env var)
    base_url="https://...",       # Optional: custom API endpoint
    timeout=60.0,                 # Optional: request timeout in seconds (default: 30)
    max_retries=3,                # Optional: retry attempts (default: 3)
)
```

## API Reference

### Personas

```python
# Create
persona = client.personas.create(name="...", dimensions=dims)

# List (paginated)
result = client.personas.list(page=1, per_page=20)

# Get
persona = client.personas.get("persona_id")

# Update
persona = client.personas.update("persona_id", name="New Name")

# Delete
client.personas.delete("persona_id")
```

### Evals

```python
# Batch evaluation
eval_run, summary = client.evals.batch(
    name="...",
    persona_id="...",
    samples=[{"id": "1", "content": "..."}],
)

# List (paginated)
result = client.evals.list(status="completed")

# Get with results
eval_run, results = client.evals.get("eval_id", include_results=True)

# Delete
client.evals.delete("eval_id")
```

### Comparisons

```python
# Create comparison
comparison = client.comparisons.create(
    baseline_eval_id="...",
    candidate_eval_id="...",
)

# List (paginated)
result = client.comparisons.list()

# Get
comparison = client.comparisons.get("comparison_id")
```

### Datasets

```python
# Create
dataset = client.datasets.create(name="...", prompts=[...])

# List (paginated)
result = client.datasets.list()

# Get
dataset = client.datasets.get("dataset_id")

# Delete
client.datasets.delete("dataset_id")
```

### Checkpoints

```python
# Create
checkpoint = client.checkpoints.create(
    name="model-v1",
    model_base="llama-3.2-8b",
    training_method="lora",
)

# List (paginated)
result = client.checkpoints.list(model_base="llama-3.2-8b")

# Get
checkpoint = client.checkpoints.get("checkpoint_id")

# Delete
client.checkpoints.delete("checkpoint_id")
```

## Documentation

Full documentation available at [lindr.io/docs](https://lindr.io/docs)

## License

MIT
