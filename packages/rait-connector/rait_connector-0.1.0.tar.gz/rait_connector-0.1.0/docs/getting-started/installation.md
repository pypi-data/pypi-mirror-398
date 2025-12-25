# Installation

## Requirements

- Python 3.9 or higher
- Azure OpenAI access
- RAIT API credentials

## Install with uv (Recommended)

```bash
uv add rait-connector
```

## Install with pip

```bash
pip install rait-connector
```

## Environment Variables

RAIT Connector requires several environment variables to be set. You can either:

1. Set them in your system environment
2. Pass them directly to `RAITClient()`

### Required RAIT Variables

```bash
export RAIT_API_URL="https://api.raitracker.com"
export RAIT_CLIENT_ID="your-client-id"
export RAIT_CLIENT_SECRET="your-client-secret"
```

### Required Azure Variables

```bash
# Azure AD
export AZURE_CLIENT_ID="your-azure-client-id"
export AZURE_TENANT_ID="your-azure-tenant-id"
export AZURE_CLIENT_SECRET="your-azure-client-secret"

# Azure OpenAI
export AZURE_OPENAI_ENDPOINT="https://your-openai.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_DEPLOYMENT="your-deployment-name"

# Azure Resources
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-resource-group"
export AZURE_PROJECT_NAME="your-project-name"
export AZURE_ACCOUNT_NAME="your-account-name"
```

### Optional Variables

```bash
export AZURE_OPENAI_API_VERSION="2024-12-01-preview"
export AZURE_AI_PROJECT_URL="https://your-ai-project-url"
```

## Verify Installation

```python
from rait_connector import RAITClient

# This will fail if environment variables are not set
client = RAITClient()
print("RAIT Connector installed successfully!")
```

## Next Steps

- [Quick Start Guide](quickstart.md)
- [Configuration Details](configuration.md)
