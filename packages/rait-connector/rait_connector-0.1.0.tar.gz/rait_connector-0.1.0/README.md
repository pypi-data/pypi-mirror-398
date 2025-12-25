# RAIT Connector

Python library for evaluating LLM outputs across multiple ethical dimensions and performance metrics using Azure AI Evaluation services.

## Features

- **22 Evaluation Metrics** across 8 ethical dimensions
- **Parallel Execution** for faster evaluations
- **Automatic API Integration** with RAIT services
- **Type-Safe** with Pydantic models
- **Flexible Configuration** via environment variables or direct parameters
- **Batch Processing** with custom callbacks
- **Comprehensive Documentation** with examples

## Installation

```bash
pip install rait-connector
```

Or with uv:

```bash
uv add rait-connector
```

## Quick Start

```python
from rait_connector import RAITClient

# Initialize client
client = RAITClient()

# Evaluate a single prompt
result = client.evaluate(
    prompt_id="123",
    prompt_url="https://example.com/123",
    timestamp="2025-12-11T10:00:00Z",
    model_name="gpt-4",
    model_version="1.0",
    query="What is AI?",
    response="AI is artificial intelligence...",
    environment="production",
    purpose="monitoring"
)

print(f"Evaluation complete: {result['prompt_id']}")
```

## Configuration

### Environment Variables

Set required environment variables:

```bash
# RAIT API
export RAIT_API_URL="https://api.raitracker.com"
export RAIT_CLIENT_ID="your-client-id"
export RAIT_CLIENT_SECRET="your-client-secret"
```

```bash
# Azure OpenAI
export AZURE_OPENAI_ENDPOINT="https://your.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="your-deployment"
```

```bash
# Azure AD
export AZURE_CLIENT_ID="your-azure-client-id"
export AZURE_TENANT_ID="your-azure-tenant-id"
export AZURE_CLIENT_SECRET="your-azure-client-secret"
```

```bash
# Azure Resources
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_PROJECT_NAME="your-project-name"
export AZURE_ACCOUNT_NAME="your-account-name"
```

### Direct Configuration

Or pass configuration directly:

```python
client = RAITClient(
    rait_api_url="https://api.raitracker.com",
    rait_client_id="your-client-id",
    rait_client_secret="your-secret",
    azure_openai_endpoint="https://your.openai.azure.com",
    azure_openai_api_key="your-key",
    azure_openai_deployment="gpt-4",
    # ... other parameters
)
```

## Evaluation Metrics

RAIT Connector supports 22 metrics across 8 ethical dimensions:

| Dimension | Metrics |
|-----------|---------|
| **Bias and Fairness** | Hate and Unfairness |
| **Explainability and Transparency** | Ungrounded Attributes, Groundedness, Groundedness Pro |
| **Monitoring and Compliance** | Content Safety |
| **Legal and Regulatory Compliance** | Protected Materials |
| **Security and Adversarial Robustness** | Code Vulnerability |
| **Model Performance** | Coherence, Fluency, QA, Similarity, F1 Score, BLEU, GLEU, ROUGE, METEOR, Retrieval |
| **Human-AI Interaction** | Relevance, Response Completeness |
| **Social and Demographic Impact** | Sexual, Violence, Self-Harm |

## Batch Evaluation

Evaluate multiple prompts efficiently:

```python
prompts = [
    {
        "prompt_id": "001",
        "prompt_url": "https://example.com/001",
        "timestamp": "2025-12-11T10:00:00Z",
        "model_name": "gpt-4",
        "model_version": "1.0",
        "query": "What is AI?",
        "response": "AI is...",
        "environment": "production",
        "purpose": "monitoring"
    },
    # ... more prompts
]

summary = client.evaluate_batch(prompts)
print(f"Completed: {summary['successful']}/{summary['total']}")
```

### With Custom Callback

```python
def on_complete(summary):
    print(f"Success: {summary['successful']}")
    print(f"Failed: {summary['failed']}")

client.evaluate_batch(prompts, on_complete=on_complete)
```

## Parallel Execution

Control parallelism for faster evaluations:

```python
result = client.evaluate(
    ...,
    parallel=True,
    max_workers=10  # Use 10 parallel workers
)
```

## Documentation

Full documentation is available in the [docs/](docs/) directory:

- [Installation Guide](docs/getting-started/installation.md)
- [Quick Start](docs/getting-started/quickstart.md)
- [API Reference](docs/reference/client.md)
- [Examples](docs/examples/single-evaluation.md)

## Requirements

- Python 3.12+
- Azure OpenAI access
- RAIT API credentials

## Development

### Setup

Clone the repository:

```bash
git clone https://github.com/Responsible-Systems/rait-connector.git
cd rait-connector
```

Install dependencies:

```bash
uv sync --dev
```

Install pre-commit hooks:

```bash
uv tool install pre-commit
pre-commit install
```

### Project Documentation

Serve docs locally:

```bash
uv run mkdocs serve
```

Build docs:

```bash
uv run mkdocs build
```

## Contributing

Contributions are welcome! Please read our contributing guidelines.

## Support

For issues and questions:

- GitHub Issues: <https://github.com/Responsible-Systems/rait-connector/issues>

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
