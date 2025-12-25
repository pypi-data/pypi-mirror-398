# Batch Evaluation

Examples of evaluating multiple prompts in batch.

## Basic Batch Evaluation

```python
from rait_connector import RAITClient

client = RAITClient()

prompts = [
    {
        "prompt_id": "batch-001",
        "prompt_url": "https://example.com/prompt/001",
        "timestamp": "2025-12-11T10:00:00Z",
        "model_name": "gpt-4",
        "model_version": "1.0",
        "query": "What is AI?",
        "response": "AI is...",
        "environment": "production",
        "purpose": "monitoring"
    },
    {
        "prompt_id": "batch-002",
        "prompt_url": "https://example.com/prompt/002",
        "timestamp": "2025-12-11T10:01:00Z",
        "model_name": "gpt-4",
        "model_version": "1.0",
        "query": "What is ML?",
        "response": "ML is...",
        "environment": "production",
        "purpose": "monitoring"
    }
]

summary = client.evaluate_batch(prompts)

print(f"Total: {summary['total']}")
print(f"Successful: {summary['successful']}")
print(f"Failed: {summary['failed']}")
```

## Using EvaluationInput Models

```python
from rait_connector import RAITClient, EvaluationInput

client = RAITClient()

prompts = [
    EvaluationInput(
        prompt_id="batch-003",
        prompt_url="https://example.com/prompt/003",
        timestamp="2025-12-11T10:02:00Z",
        model_name="gpt-4",
        model_version="1.0",
        query="What is deep learning?",
        response="Deep learning is...",
        environment="production",
        purpose="monitoring"
    ),
    EvaluationInput(
        prompt_id="batch-004",
        prompt_url="https://example.com/prompt/004",
        timestamp="2025-12-11T10:03:00Z",
        model_name="gpt-4",
        model_version="1.0",
        query="What is neural network?",
        response="A neural network is...",
        environment="production",
        purpose="monitoring"
    )
]

summary = client.evaluate_batch(prompts)
```

## With Custom Callback

```python
def on_complete(summary):
    print(f"Batch evaluation complete!")
    print(f"Success rate: {summary['successful']}/{summary['total']}")

    if summary['errors']:
        print("\nErrors:")
        for error in summary['errors']:
            print(f"  - {error['prompt_id']}: {error['error']}")

summary = client.evaluate_batch(
    prompts,
    on_complete=on_complete
)
```

## Processing Results

```python
summary = client.evaluate_batch(prompts)

# Process successful results
for result in summary['results']:
    print(f"\nProcessing {result['prompt_id']}")

    for dimension in result['ethical_dimensions']:
        print(f"  {dimension['dimension_name']}")

        for metric in dimension['dimension_metrics']:
            print(f"    - {metric['metric_name']}")

# Handle errors
for error in summary['errors']:
    print(f"Failed: {error['prompt_id']} - {error['error']}")
```

## Fail Fast Mode

```python
from rait_connector.exceptions import EvaluationError

try:
    summary = client.evaluate_batch(
        prompts,
        fail_fast=True  # Stop on first error
    )
except EvaluationError as e:
    print(f"Batch failed: {e}")
```

## Parallel Configuration

```python
# Increase workers for better performance
summary = client.evaluate_batch(
    prompts,
    parallel=True,
    max_workers=10
)

# Or disable parallel execution
summary = client.evaluate_batch(
    prompts,
    parallel=False
)
```

## Loading from CSV

```python
import csv
from datetime import datetime

prompts = []

with open('prompts.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        prompts.append({
            "prompt_id": row['id'],
            "prompt_url": row['url'],
            "timestamp": datetime.now().isoformat(),
            "model_name": row['model'],
            "model_version": row['version'],
            "query": row['query'],
            "response": row['response'],
            "environment": "production",
            "purpose": "batch_monitoring"
        })

summary = client.evaluate_batch(prompts)
```

## Loading from JSON

```python
import json

with open('prompts.json', 'r') as f:
    prompts = json.load(f)

summary = client.evaluate_batch(prompts)
```

## Saving Results

```python
import json

summary = client.evaluate_batch(prompts)

# Save summary
with open('batch_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Save detailed results
for result in summary['results']:
    filename = f"result_{result['prompt_id']}.json"
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)
```

## Progress Tracking

```python
def track_progress(summary):
    total = summary['total']
    success = summary['successful']
    failed = summary['failed']

    print(f"\nBatch Complete: {success + failed}/{total}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Success Rate: {success/total*100:.1f}%")

summary = client.evaluate_batch(
    prompts,
    on_complete=track_progress
)
```

## Batch with Retry Logic

```python
from rait_connector.exceptions import EvaluationError

max_retries = 3

for attempt in range(max_retries):
    try:
        summary = client.evaluate_batch(prompts)

        if summary['failed'] == 0:
            print("All evaluations successful!")
            break

        # Retry only failed prompts
        failed_ids = {e['prompt_id'] for e in summary['errors']}
        prompts = [p for p in prompts if p['prompt_id'] in failed_ids]

        print(f"Retrying {len(prompts)} failed prompts (attempt {attempt + 1})")

    except EvaluationError as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        if attempt == max_retries - 1:
            raise
```
