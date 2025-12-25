"""Base classes for metric evaluators."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..constants import Metric


class BaseEvaluator(ABC):
    """Abstract base class for all metric evaluators.

    Each evaluator implements a specific metric evaluation using
    Azure AI evaluation services.

    Attributes:
        metric_name: The Metric enum value this evaluator handles
        requires_context: Whether this evaluator needs context field
        requires_ground_truth: Whether this evaluator needs ground_truth field
    """

    metric_name: Metric
    requires_context: bool = False
    requires_ground_truth: bool = False

    def __init__(self, model_config=None, azure_ai_project=None, credential=None):
        """Initialize the evaluator with Azure configuration.

        Args:
            model_config: Azure OpenAI model configuration
            azure_ai_project: Azure AI project configuration dict
            credential: Azure credential for authentication
        """
        self.model_config = model_config
        self.azure_ai_project = azure_ai_project
        self.credential = credential

    @abstractmethod
    def evaluate(
        self,
        query: str,
        response: str,
        context: Optional[str] = None,
        ground_truth: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate the metric for given inputs.

        Args:
            query: User's input query
            response: LLM's generated response
            context: Additional context (optional)
            ground_truth: Expected response (optional)

        Returns:
            Dict containing the evaluation result with metric score/label

        Raises:
            EvaluationError: If evaluation fails
        """
        pass

    def can_evaluate(self, has_context: bool, has_ground_truth: bool) -> bool:
        """Check if this evaluator can run with available data.

        Args:
            has_context: Whether context is available
            has_ground_truth: Whether ground_truth is available

        Returns:
            True if evaluator can run with available data
        """
        if self.requires_context and not has_context:
            return False
        if self.requires_ground_truth and not has_ground_truth:
            return False
        return True


__all__ = ["BaseEvaluator"]
