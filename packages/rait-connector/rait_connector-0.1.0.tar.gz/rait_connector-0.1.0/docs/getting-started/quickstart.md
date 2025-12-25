# Quick Start

This guide will walk you through your first evaluation with RAIT Connector.

## Step 1: Import and Initialize

```python
from rait_connector import RAITClient

# Initialize client (reads from environment variables)
client = RAITClient()
```

## Step 2: Prepare Your Data

```python
prompt_data = {
    "prompt_id": "eval-001",
    "prompt_url": "https://example.com/prompt/001",
    "timestamp": "2025-12-11T10:00:00Z",
    "model_name": "gpt-4",
    "model_version": "1.0",
    "query": "What are the ethical implications of AI?",
    "response": "AI has several ethical implications including privacy concerns...",
    "ground_truth": "Expected answer for comparison",
    "context": "Additional context about the query",
    "environment": "production",
    "purpose": "quality_monitoring",
    "metadata": {
        "latency_ms": 850,
        "tokens": 120
    }
}
```

## Step 3: Run Evaluation

```python
# Evaluate and automatically post results
result = client.evaluate(**prompt_data)

print(f"Evaluation completed for {result['prompt_id']}")
print(f"Status: {result['post_response']['status_code']}")
```

## Step 4: Check Results

```python
# Access ethical dimensions
for dimension in result['ethical_dimensions']:
    print(f"\n{dimension['dimension_name']}:")
    for metric in dimension['dimension_metrics']:
        print(f"  - {metric['metric_name']}: {metric.get('metric_metadata', {})}")
```

## Batch Evaluation

Evaluate multiple prompts at once:

```python
prompts = [prompt_data_1, prompt_data_2, prompt_data_3]

summary = client.evaluate_batch(prompts)

print(f"Completed: {summary['successful']}/{summary['total']}")
print(f"Failed: {summary['failed']}")
```

## With Custom Callback

```python
def on_batch_complete(summary):
    print(f"Batch evaluation complete!")
    print(f"  Success: {summary['successful']}")
    print(f"  Failed: {summary['failed']}")

    for error in summary['errors']:
        print(f"  Error in {error['prompt_id']}: {error['error']}")

client.evaluate_batch(prompts, on_complete=on_batch_complete)
```

## Parallel Execution

Control parallelism for faster evaluations:

```python
result = client.evaluate(
    **prompt_data,
    parallel=True,      # Enable parallel evaluation
    max_workers=10      # Use 10 parallel workers
)
```

## Next Steps

- [Configuration Guide](configuration.md)
- [API Reference](../reference/client.md)
- [More Examples](../examples/single-evaluation.md)
