"""Constants used throughout the RAIT Connector library."""

from enum import Enum


class Metric(str, Enum):
    """Enumeration of metric names used for model evaluation.

    Each value corresponds to a specific scoring category used
    to assess model behavior, safety, quality, robustness, or
    task performance.
    """

    HATE_AND_UNFAIRNESS = "Hate and Unfairness"
    UNGROUNDED_ATTRIBUTES = "Ungrounded Attributes"
    CONTENT_SAFETY = "Content Safety"
    PROTECTED_MATERIALS = "Protected Materials"
    CODE_VULNERABILITY = "Code Vulnerability"
    COHERENCE = "Coherence"
    FLUENCY = "Fluency"
    QA = "QA"
    SIMILARITY = "Similarity"
    F1_SCORE = "F1 Score"
    BLEU = "BLEU"
    GLEU = "GLEU"
    ROUGE = "ROUGE"
    METEOR = "METEOR"
    RETRIEVAL = "Retrieval"
    GROUNDEDNESS = "Groundedness"
    GROUNDEDNESS_PRO = "Groundedness Pro"
    RELEVANCE = "Relevance"
    RESPONSE_COMPLETENESS = "Response Completeness"
    SEXUAL = "Sexual"
    VIOLENCE = "Violence"
    SELF_HARM = "Self-Harm"


__all__ = ["Metric"]
