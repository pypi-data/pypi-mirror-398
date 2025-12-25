# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-22

### Added

- Initial release of RAIT Connector
- RAITClient for LLM evaluation across ethical dimensions
- Support for 22 evaluation metrics across 8 ethical dimensions:
  - Bias and Fairness: Hate and Unfairness
  - Explainability and Transparency: Ungrounded Attributes, Groundedness, Groundedness Pro
  - Monitoring and Compliance: Content Safety
  - Legal and Regulatory Compliance: Protected Materials
  - Security and Adversarial Robustness: Code Vulnerability
  - Model Performance: Coherence, Fluency, QA, Similarity, F1 Score, BLEU, GLEU, ROUGE, METEOR, Retrieval
  - Human-AI Interaction: Relevance, Response Completeness
  - Social and Demographic Impact: Sexual, Violence, Self-Harm
- Parallel evaluation support with configurable workers
- Automatic result posting to RAIT API with encryption
- Batch evaluation with custom callbacks
- Type-safe data validation with Pydantic
- Flexible configuration via environment variables or direct parameters
- Comprehensive documentation with examples
