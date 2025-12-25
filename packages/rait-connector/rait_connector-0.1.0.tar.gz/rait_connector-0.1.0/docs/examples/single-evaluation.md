# Single Evaluation

Examples of evaluating a single prompt.

## Basic Evaluation

```python
from rait_connector import RAITClient

client = RAITClient()

result = client.evaluate(
    prompt_id="eval-001",
    prompt_url="https://example.com/prompt/001",
    timestamp="2025-12-11T10:00:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is artificial intelligence?",
    response="Artificial intelligence is the simulation of human intelligence...",
    environment="production",
    purpose="quality_monitoring"
)

print(f"Evaluation complete: {result['prompt_id']}")
print(f"API Status: {result['post_response']['status_code']}")
```

## With Ground Truth and Context

```python
result = client.evaluate(
    prompt_id="eval-002",
    prompt_url="https://example.com/prompt/002",
    timestamp="2025-12-11T10:05:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What are the benefits of renewable energy?",
    response="Renewable energy reduces carbon emissions...",
    ground_truth="Renewable energy sources like solar and wind...",
    context="Discussion about climate change and sustainability",
    environment="production",
    purpose="accuracy_testing"
)
```

## With Metadata

```python
result = client.evaluate(
    prompt_id="eval-003",
    prompt_url="https://example.com/prompt/003",
    timestamp="2025-12-11T10:10:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="Explain quantum computing",
    response="Quantum computing uses quantum mechanics...",
    environment="production",
    purpose="monitoring",
    metadata={
        "latency_ms": 1250,
        "tokens_prompt": 45,
        "tokens_completion": 120,
        "total_tokens": 165,
        "user_id": "user_123",
        "session_id": "session_456"
    }
)
```

## Parallel Execution

```python
# Use more workers for faster evaluation
result = client.evaluate(
    prompt_id="eval-004",
    prompt_url="https://example.com/prompt/004",
    timestamp="2025-12-11T10:15:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is machine learning?",
    response="Machine learning is a subset of AI...",
    environment="production",
    purpose="monitoring",
    parallel=True,
    max_workers=10
)
```

## Sequential Execution

```python
# Disable parallel execution for debugging
result = client.evaluate(
    prompt_id="eval-005",
    prompt_url="https://example.com/prompt/005",
    timestamp="2025-12-11T10:20:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is deep learning?",
    response="Deep learning uses neural networks...",
    environment="development",
    purpose="debugging",
    parallel=False
)
```

## Fail Fast Mode

```python
from rait_connector.exceptions import EvaluationError

try:
    result = client.evaluate(
        prompt_id="eval-006",
        prompt_url="https://example.com/prompt/006",
        timestamp="2025-12-11T10:25:00Z",
        model_name="gpt-4",
        model_version="1.0",
        query="What is neural network?",
        response="A neural network is...",
        environment="production",
        purpose="monitoring",
        fail_fast=True  # Stop on first error
    )
except EvaluationError as e:
    print(f"Evaluation failed: {e}")
```

## Accessing Results

```python
result = client.evaluate(...)

# Access prompt data
print(f"Prompt ID: {result['prompt_id']}")
print(f"Model: {result['model_name']} v{result['model_version']}")

# Access ethical dimensions
for dimension in result['ethical_dimensions']:
    print(f"\nDimension: {dimension['dimension_name']}")

    for metric in dimension['dimension_metrics']:
        metric_name = metric['metric_name']
        metadata = metric.get('metric_metadata', {})
        print(f"  {metric_name}: {metadata}")

# Check API response
post_response = result['post_response']
print(f"\nAPI Response: {post_response['status_code']}")
```

## With Connector Logs

```python
import logging
from io import StringIO

# Capture logs
log_stream = StringIO()
handler = logging.StreamHandler(log_stream)
logging.getLogger('rait_connector').addHandler(handler)

result = client.evaluate(
    prompt_id="eval-007",
    prompt_url="https://example.com/prompt/007",
    timestamp="2025-12-11T10:30:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is AI ethics?",
    response="AI ethics involves...",
    environment="production",
    purpose="monitoring",
    connector_logs=log_stream.getvalue()
)
```
