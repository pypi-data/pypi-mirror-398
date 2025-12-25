# Configuration

RAIT Connector can be configured in two ways:

1. **Environment Variables** (recommended for production)
2. **Direct Parameters** (useful for testing or multiple configurations)

## Using Environment Variables

Set environment variables in your system or deployment:

```bash
# RAIT Configuration
export RAIT_API_URL="https://api.raitracker.com"
export RAIT_CLIENT_ID="your-client-id"
export RAIT_CLIENT_SECRET="your-secret"

# Azure Configuration
export AZURE_OPENAI_ENDPOINT="https://your.openai.azure.com"
export AZURE_OPENAI_API_KEY="your-key"
# ... more variables
```

Then initialize without parameters:

```python
from rait_connector import RAITClient

client = RAITClient()  # Reads from environment
```

## Using Direct Parameters

Pass configuration directly (overrides environment variables):

```python
from rait_connector import RAITClient

client = RAITClient(
    rait_api_url="https://api.raitracker.com",
    rait_client_id="your-client-id",
    rait_client_secret="your-secret",
    azure_openai_endpoint="https://your.openai.azure.com",
    azure_openai_api_key="your-key",
    azure_openai_deployment="gpt-4",
    # ... more parameters
)
```

## Configuration Precedence

1. **Direct parameters** to `RAITClient()` (highest priority)
2. **Environment variables**
3. **Default values** (only for optional settings)

## RAIT Settings

| Parameter            | Environment Variable | Required | Description                  |
| -------------------- | -------------------- | -------- | ---------------------------- |
| `rait_api_url`       | `RAIT_API_URL`       | Yes      | RAIT API endpoint            |
| `rait_client_id`     | `RAIT_CLIENT_ID`     | Yes      | Client ID for authentication |
| `rait_client_secret` | `RAIT_CLIENT_SECRET` | Yes      | Client secret                |

## Azure Settings

### Authentication

| Parameter             | Environment Variable  | Required | Description            |
| --------------------- | --------------------- | -------- | ---------------------- |
| `azure_client_id`     | `AZURE_CLIENT_ID`     | Yes      | Azure AD client ID     |
| `azure_tenant_id`     | `AZURE_TENANT_ID`     | Yes      | Azure AD tenant ID     |
| `azure_client_secret` | `AZURE_CLIENT_SECRET` | Yes      | Azure AD client secret |

### OpenAI

| Parameter                  | Environment Variable       | Required | Description                                 |
| -------------------------- | -------------------------- | -------- | ------------------------------------------- |
| `azure_openai_endpoint`    | `AZURE_OPENAI_ENDPOINT`    | Yes      | OpenAI endpoint URL                         |
| `azure_openai_api_key`     | `AZURE_OPENAI_API_KEY`     | Yes      | OpenAI API key                              |
| `azure_openai_deployment`  | `AZURE_OPENAI_DEPLOYMENT`  | Yes      | Deployment name                             |
| `azure_openai_api_version` | `AZURE_OPENAI_API_VERSION` | No       | API version (default: `2024-12-01-preview`) |

### Resources

| Parameter               | Environment Variable    | Required | Description     |
| ----------------------- | ----------------------- | -------- | --------------- |
| `azure_subscription_id` | `AZURE_SUBSCRIPTION_ID` | Yes      | Subscription ID |
| `azure_resource_group`  | `AZURE_RESOURCE_GROUP`  | Yes      | Resource group  |
| `azure_project_name`    | `AZURE_PROJECT_NAME`    | Yes      | AI project name |
| `azure_account_name`    | `AZURE_ACCOUNT_NAME`    | Yes      | Account name    |
| `azure_ai_project_url`  | `AZURE_AI_PROJECT_URL`  | No       | AI project URL  |

## Multiple Configurations

Create multiple clients with different configurations:

```python
# Production client
prod_client = RAITClient(
    rait_api_url="https://api.raitracker.com",
    rait_client_id="prod-client-id",
    rait_client_secret="prod-secret"
)

# Development client
dev_client = RAITClient(
    rait_api_url="https://api.raitracker.com",
    rait_client_id="dev-client-id",
    rait_client_secret="dev-secret"
)
```

## Best Practices

1. **Use environment variables in production** for security
2. **Never commit credentials** to version control
3. **Use separate credentials** for dev/staging/prod
4. **Validate configuration** on startup
5. **Use direct parameters** for testing and CI/CD

## Validation

Check if configuration is valid:

```python
from rait_connector import RAITClient
from rait_connector.exceptions import AuthenticationError

try:
    client = RAITClient()
    metrics = client.get_enabled_metrics()
    print(f"Configuration valid! Found {len(metrics)} metric dimensions")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except Exception as e:
    print(f"Configuration error: {e}")
```
