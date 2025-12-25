"""RAIT Connector - Python library for LLM evaluation with RAIT API.

This library provides tools for evaluating LLM outputs across multiple
ethical dimensions and performance metrics using Azure AI Evaluation services.

Example:
    >>> from rait_connector import RAITClient
    >>>
    >>> client = RAITClient()
    >>>
    >>> result = client.evaluate(
    ...     prompt_id="123",
    ...     prompt_url="https://example.com/123",
    ...     timestamp="2025-01-01T00:00:00Z",
    ...     model_name="gpt-4",
    ...     model_version="1.0",
    ...     query="What is AI?",
    ...     response="AI is artificial intelligence...",
    ...     environment="production",
    ...     purpose="monitoring"
    ... )
"""

from .client import RAITClient
from .config import Settings, settings
from .constants import Metric
from .exceptions import (
    AuthenticationError,
    EncryptionError,
    EvaluationError,
    MetricsError,
    RAITConnectorError,
)
from .models import EvaluationInput

__version__ = "0.1.0"

__all__ = [
    "RAITClient",
    "Settings",
    "settings",
    "Metric",
    "EvaluationInput",
    "RAITConnectorError",
    "AuthenticationError",
    "EncryptionError",
    "EvaluationError",
    "MetricsError",
]
