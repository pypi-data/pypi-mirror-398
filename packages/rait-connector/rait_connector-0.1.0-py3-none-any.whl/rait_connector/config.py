"""Application settings and configuration management.

This module handles all environment variable loading and validation
using Pydantic Settings for type safety and automatic validation.
"""

from typing import Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All settings can be loaded from environment variables or passed
    directly to RAITClient. Values passed to RAITClient take precedence.
    """

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",
    )

    rait_api_url: Optional[str] = Field(
        default=None, alias="RAIT_API_URL", description="RAIT API endpoint URL"
    )

    rait_client_id: Optional[str] = Field(
        default=None, alias="RAIT_CLIENT_ID", description="RAIT client ID"
    )

    rait_client_secret: Optional[str] = Field(
        default=None, alias="RAIT_CLIENT_SECRET", description="RAIT client secret"
    )

    azure_client_id: Optional[str] = Field(
        default=None, alias="AZURE_CLIENT_ID", description="Azure AD client ID"
    )

    azure_tenant_id: Optional[str] = Field(
        default=None, alias="AZURE_TENANT_ID", description="Azure AD tenant ID"
    )

    azure_client_secret: Optional[str] = Field(
        default=None, alias="AZURE_CLIENT_SECRET", description="Azure AD client secret"
    )

    azure_openai_endpoint: Optional[str] = Field(
        default=None,
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL",
    )

    azure_openai_api_key: Optional[str] = Field(
        default=None, alias="AZURE_OPENAI_API_KEY", description="Azure OpenAI API key"
    )

    azure_openai_deployment: Optional[str] = Field(
        default=None,
        alias="AZURE_OPENAI_DEPLOYMENT",
        description="Azure OpenAI deployment",
    )

    azure_openai_api_version: str = Field(
        default="2024-12-01-preview", description="Azure OpenAI API version"
    )

    azure_subscription_id: Optional[str] = Field(
        default=None, alias="AZURE_SUBSCRIPTION_ID", description="Azure subscription ID"
    )

    azure_resource_group: Optional[str] = Field(
        default=None, alias="AZURE_RESOURCE_GROUP", description="Azure resource group"
    )

    azure_project_name: Optional[str] = Field(
        default=None, alias="AZURE_PROJECT_NAME", description="Azure AI project name"
    )

    azure_account_name: Optional[str] = Field(
        default=None, alias="AZURE_ACCOUNT_NAME", description="Azure account name"
    )

    azure_ai_project_url: Optional[str] = Field(
        default=None, alias="AZURE_AI_PROJECT_URL", description="Azure AI project URL"
    )

    def _set_azure_env_vars(self):
        """Set Azure AD credentials as environment variables if available."""
        if self.azure_client_id:
            os.environ["AZURE_CLIENT_ID"] = self.azure_client_id
        if self.azure_tenant_id:
            os.environ["AZURE_TENANT_ID"] = self.azure_tenant_id
        if self.azure_client_secret:
            os.environ["AZURE_CLIENT_SECRET"] = self.azure_client_secret

    @model_validator(mode="after")
    def set_azure_env_vars(self):
        """Set Azure AD credentials as environment variables if available.

        This ensures DefaultAzureCredential can access them directly
        from the environment.
        """
        self._set_azure_env_vars()
        return self

    @field_validator("azure_openai_endpoint", "rait_api_url", "azure_ai_project_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Ensure URLs are properly formatted without trailing slashes.

        Args:
            v: URL string to validate

        Returns:
            Validated URL without trailing slash or None
        """
        if not v:
            return None
        return v.rstrip("/")

    @field_validator(
        "azure_openai_api_key", "rait_client_secret", "azure_client_secret"
    )
    @classmethod
    def validate_secrets(cls, v: Optional[str]) -> Optional[str]:
        """Ensure secrets are not empty if provided.

        Args:
            v: Secret string to validate

        Returns:
            Validated secret or None

        Raises:
            ValueError: If secret is provided but empty
        """
        if not v:
            return None
        if v.strip() == "":
            raise ValueError("Secret cannot be empty string")
        return v

    def get_azure_ai_project_dict(self) -> dict:
        """Get Azure AI project configuration as dictionary.

        Returns:
            Azure AI project configuration

        Raises:
            ValueError: If required Azure fields are not set
        """
        if not all(
            [
                self.azure_subscription_id,
                self.azure_resource_group,
                self.azure_project_name,
            ]
        ):
            raise ValueError(
                "Azure subscription_id, resource_group, and project_name are required"
            )

        return {
            "subscription_id": self.azure_subscription_id,
            "resource_group_name": self.azure_resource_group,
            "project_name": self.azure_project_name,
        }

    def get_auth_headers(self, token: str) -> dict:
        """Get standard authentication headers.

        Args:
            token: Bearer token for authentication

        Returns:
            Headers dictionary with authorization
        """
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def merge_with(self, **overrides) -> "Settings":
        """Create a new Settings instance with overridden values.

        Args:
            **overrides: Key-value pairs to override

        Returns:
            New Settings instance with merged values
        """
        filtered_overrides = {k: v for k, v in overrides.items() if v is not None}
        new_settings = self.model_copy(update=filtered_overrides)
        new_settings._set_azure_env_vars()  # Explicitly set env vars after copy
        return new_settings


settings = Settings()
