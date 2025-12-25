"""Registry for mapping metric names to evaluator implementations."""

import logging
from typing import Any, Dict, Optional

from azure.ai.evaluation import (
    BleuScoreEvaluator,
    CodeVulnerabilityEvaluator,
    CoherenceEvaluator,
    ContentSafetyEvaluator,
    F1ScoreEvaluator,
    FluencyEvaluator,
    GleuScoreEvaluator,
    GroundednessEvaluator,
    GroundednessProEvaluator,
    HateUnfairnessEvaluator,
    MeteorScoreEvaluator,
    ProtectedMaterialEvaluator,
    QAEvaluator,
    RelevanceEvaluator,
    ResponseCompletenessEvaluator,
    RetrievalEvaluator,
    RougeScoreEvaluator,
    RougeType,
    SelfHarmEvaluator,
    SexualEvaluator,
    SimilarityEvaluator,
    UngroundedAttributesEvaluator,
    ViolenceEvaluator,
)

from ..constants import Metric
from ..exceptions import EvaluationError

logger = logging.getLogger(__name__)


EVALUATOR_CONFIG = {
    Metric.HATE_AND_UNFAIRNESS: {
        "class": HateUnfairnessEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.UNGROUNDED_ATTRIBUTES: {
        "class": UngroundedAttributesEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": True,
        "requires_ground_truth": False,
    },
    Metric.CONTENT_SAFETY: {
        "class": ContentSafetyEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.PROTECTED_MATERIALS: {
        "class": ProtectedMaterialEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.CODE_VULNERABILITY: {
        "class": CodeVulnerabilityEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.COHERENCE: {
        "class": CoherenceEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.FLUENCY: {
        "class": FluencyEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.QA: {
        "class": QAEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": True,
        "requires_ground_truth": True,
    },
    Metric.SIMILARITY: {
        "class": SimilarityEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.F1_SCORE: {
        "class": F1ScoreEvaluator,
        "needs_project": False,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.BLEU: {
        "class": BleuScoreEvaluator,
        "needs_project": False,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.GLEU: {
        "class": GleuScoreEvaluator,
        "needs_project": False,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.ROUGE: {
        "class": RougeScoreEvaluator,
        "needs_project": False,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.METEOR: {
        "class": MeteorScoreEvaluator,
        "needs_project": False,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.RETRIEVAL: {
        "class": RetrievalEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": True,
        "requires_ground_truth": False,
    },
    Metric.GROUNDEDNESS: {
        "class": GroundednessEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": True,
        "requires_ground_truth": False,
    },
    Metric.GROUNDEDNESS_PRO: {
        "class": GroundednessProEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": True,
        "requires_ground_truth": False,
    },
    Metric.RELEVANCE: {
        "class": RelevanceEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.RESPONSE_COMPLETENESS: {
        "class": ResponseCompletenessEvaluator,
        "needs_project": False,
        "needs_model_config": True,
        "requires_context": False,
        "requires_ground_truth": True,
    },
    Metric.SEXUAL: {
        "class": SexualEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.VIOLENCE: {
        "class": ViolenceEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
    Metric.SELF_HARM: {
        "class": SelfHarmEvaluator,
        "needs_project": True,
        "needs_model_config": False,
        "requires_context": False,
        "requires_ground_truth": False,
    },
}


def create_evaluator(
    metric_name: str,
    model_config: Optional[Any] = None,
    azure_ai_project: Optional[Dict[str, str]] = None,
    credential: Optional[Any] = None,
) -> Any:
    """Create an evaluator instance for a given metric name.

    Args:
        metric_name: Name of the metric (case-insensitive)
        model_config: Azure OpenAI model configuration
        azure_ai_project: Azure AI project configuration
        credential: Azure credential

    Returns:
        Configured evaluator instance

    Raises:
        EvaluationError: If metric not found or initialization fails
    """
    metric_enum = None
    metric_name_lower = metric_name.lower()

    for metric in Metric:
        if metric.value.lower() == metric_name_lower:
            metric_enum = metric
            break

    if not metric_enum or metric_enum not in EVALUATOR_CONFIG:
        raise EvaluationError(f"Unknown metric: {metric_name}")

    config = EVALUATOR_CONFIG[metric_enum]
    evaluator_class = config["class"]

    try:
        kwargs = {}

        if config["needs_model_config"] and model_config:
            kwargs["model_config"] = model_config

        if config["needs_project"] and azure_ai_project:
            kwargs["azure_ai_project"] = azure_ai_project
            if credential:
                kwargs["credential"] = credential

        if metric_enum == Metric.ROUGE:
            kwargs["rouge_type"] = RougeType.ROUGE_L

        evaluator = evaluator_class(**kwargs)
        logger.debug(f"Created evaluator for {metric_name}")

        return evaluator

    except Exception as e:
        raise EvaluationError(
            f"Failed to create evaluator for {metric_name}: {e}"
        ) from e


def can_evaluate_metric(
    metric_name: str,
    has_context: bool,
    has_ground_truth: bool,
) -> bool:
    """Check if a metric can be evaluated with available data.

    Args:
        metric_name: Name of the metric
        has_context: Whether context is available
        has_ground_truth: Whether ground_truth is available

    Returns:
        True if metric can be evaluated
    """
    metric_enum = None
    metric_name_lower = metric_name.lower()

    for metric in Metric:
        if metric.value.lower() == metric_name_lower:
            metric_enum = metric
            break

    if not metric_enum or metric_enum not in EVALUATOR_CONFIG:
        return False

    config = EVALUATOR_CONFIG[metric_enum]

    if config["requires_context"] and not has_context:
        return False
    if config["requires_ground_truth"] and not has_ground_truth:
        return False

    return True


__all__ = ["create_evaluator", "can_evaluate_metric", "EVALUATOR_CONFIG"]
