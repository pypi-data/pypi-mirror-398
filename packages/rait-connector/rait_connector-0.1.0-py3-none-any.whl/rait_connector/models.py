"""Data models for RAIT Connector.

This module defines Pydantic models for type-safe data validation.
"""

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field, field_validator


class EvaluationInput(BaseModel):
    """Input data for LLM evaluation.

    Attributes:
        prompt_id: Unique identifier for the prompt
        prompt_url: URL reference to the prompt
        timestamp: ISO 8601 timestamp
        model_name: Name of the LLM model used
        model_version: Version of the LLM model
        query: The user's input query/prompt
        response: The LLM's generated response
        ground_truth: Expected response for comparison
        context: Additional context provided to the LLM
        metadata: Arbitrary metadata dictionary
        environment: Environment where prompt was executed
        purpose: Purpose of the evaluation
    """

    prompt_id: str
    prompt_url: str
    timestamp: str
    model_name: str
    model_version: str
    query: str
    response: str
    ground_truth: str = ""
    context: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    environment: str
    purpose: str

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate timestamp is in ISO 8601 format.

        Args:
            v: Timestamp string

        Returns:
            Validated timestamp

        Raises:
            ValueError: If timestamp format is invalid
        """
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError as e:
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}") from e
        return v


__all__ = ["EvaluationInput"]
