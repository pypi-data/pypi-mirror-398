# RAIT Connector

Python library for evaluating LLM outputs across multiple ethical dimensions and performance metrics using Azure AI Evaluation services.

## Features

- **22 Evaluation Metrics** across 8 ethical dimensions
- **Parallel Execution** for faster evaluations
- **Automatic API Integration** with RAIT services
- **Type-Safe** with Pydantic models
- **Flexible Configuration** via environment variables or direct parameters

## Quick Example

```python
from rait_connector import RAITClient

# Initialize client
client = RAITClient()

# Evaluate a single prompt
result = client.evaluate(
    prompt_id="123",
    prompt_url="https://example.com/123",
    timestamp="2025-01-01T00:00:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is AI?",
    response="AI is artificial intelligence...",
    environment="production",
    purpose="monitoring"
)
```

## Installation

```bash
uv add rait-connector
```

Or with pip:

```bash
pip install rait-connector
```

## Next Steps

- [Getting Started](getting-started/installation.md) - Installation and setup
- [Quick Start](getting-started/quickstart.md) - Your first evaluation
- [API Reference](reference/client.md) - Complete API documentation
- [Examples](examples/single-evaluation.md) - Code examples
