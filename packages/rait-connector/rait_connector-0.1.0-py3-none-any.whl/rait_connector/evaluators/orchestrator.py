"""Orchestrator for running metric evaluations in parallel."""

import copy
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, Union

from ..exceptions import EvaluationError
from .registry import can_evaluate_metric, create_evaluator

logger = logging.getLogger(__name__)


class EvaluatorOrchestrator:
    """Orchestrates parallel evaluation of multiple metrics.

    This class manages the execution of multiple metric evaluators,
    optionally running them in parallel to reduce total evaluation time.

    Attributes:
        model_config: Azure OpenAI model configuration
        azure_ai_project: Azure AI project configuration
        credential: Azure credential for authentication
    """

    def __init__(
        self,
        model_config: Optional[Any] = None,
        azure_ai_project: Optional[Union[str, Dict[str, str]]] = None,
        credential: Optional[Any] = None,
    ):
        """Initialize the orchestrator with Azure configuration.

        Args:
            model_config: Azure OpenAI model configuration
            azure_ai_project: Azure AI project configuration dict or URL
            credential: Azure credential for authentication
        """
        self.model_config = model_config
        self.azure_ai_project = azure_ai_project
        self.credential = credential

    def _evaluate_single_metric(
        self,
        metric_name: str,
        metric_id: str,
        query: str,
        response: str,
        context: str,
        ground_truth: str,
    ) -> Tuple[str, str, Optional[Dict[str, Any]], Optional[Exception]]:
        """Evaluate a single metric.

        Args:
            metric_name: Name of the metric to evaluate
            metric_id: ID of the metric
            query: User's query
            response: LLM's response
            context: Additional context
            ground_truth: Expected response

        Returns:
            Tuple of (metric_name, metric_id, result_dict, error)
        """
        try:
            has_context = bool(context)
            has_ground_truth = bool(ground_truth)

            if not can_evaluate_metric(metric_name, has_context, has_ground_truth):
                logger.debug(f"Skipping {metric_name} - missing required data")
                return metric_name, metric_id, None, None

            evaluator = create_evaluator(
                metric_name,
                model_config=self.model_config,
                azure_ai_project=self.azure_ai_project,
                credential=self.credential,
            )

            eval_args = {"query": query, "response": response}

            if has_context:
                eval_args["context"] = context
            if has_ground_truth:
                eval_args["ground_truth"] = ground_truth

            result = evaluator(**eval_args)

            logger.info(f"{metric_name}: {result}")
            return metric_name, metric_id, result, None

        except Exception as e:
            logger.error(f"{metric_name}: {e}")
            return metric_name, metric_id, None, e

    def evaluate_metrics(
        self,
        prompt_data: Dict[str, str],
        ethical_dimensions: List[Dict[str, Any]],
        parallel: bool = True,
        max_workers: int = 5,
        fail_fast: bool = False,
    ) -> List[Dict[str, Any]]:
        """Evaluate all enabled metrics for a prompt.

        Args:
            prompt_data: Dict with query, response, context, ground_truth
            ethical_dimensions: List of ethical dimensions with metrics config
            parallel: Whether to run evaluations in parallel
            max_workers: Maximum number of parallel workers
            fail_fast: Whether to stop on first error

        Returns:
            Updated ethical dimensions with evaluation results

        Raises:
            EvaluationError: If fail_fast=True and any evaluation fails
        """
        dimensions = copy.deepcopy(ethical_dimensions)

        query = prompt_data.get("query", "")
        response = prompt_data.get("response", "")
        context = prompt_data.get("context", "")
        ground_truth = prompt_data.get("ground_truth", "")

        metrics_to_evaluate = []
        for dimension in dimensions:
            for metric in dimension.get("dimension_metrics", []):
                metrics_to_evaluate.append(
                    {
                        "metric_name": metric.get("metric_name"),
                        "metric_id": metric.get("metric_id"),
                    }
                )

        logger.info(f"Evaluating {len(metrics_to_evaluate)} metrics")

        if parallel and len(metrics_to_evaluate) > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._evaluate_single_metric,
                        m["metric_name"],
                        m["metric_id"],
                        query,
                        response,
                        context,
                        ground_truth,
                    ): m
                    for m in metrics_to_evaluate
                }

                for future in as_completed(futures):
                    metric_name, metric_id, result, error = future.result()

                    if error:
                        if fail_fast:
                            raise EvaluationError(
                                f"Evaluation failed for {metric_name}: {error}"
                            ) from error
                        continue

                    if result:
                        self._update_metric_result(dimensions, metric_id, result)
        else:
            for m in metrics_to_evaluate:
                metric_name, metric_id, result, error = self._evaluate_single_metric(
                    m["metric_name"],
                    m["metric_id"],
                    query,
                    response,
                    context,
                    ground_truth,
                )

                if error:
                    if fail_fast:
                        raise EvaluationError(
                            f"Evaluation failed for {metric_name}: {error}"
                        ) from error
                    continue

                if result:
                    self._update_metric_result(dimensions, metric_id, result)

        return dimensions

    def _update_metric_result(
        self,
        dimensions: List[Dict[str, Any]],
        metric_id: str,
        result: Dict[str, Any],
    ):
        """Update a metric's result in the dimensions structure.

        Args:
            dimensions: List of ethical dimensions
            metric_id: ID of the metric to update
            result: Evaluation result dictionary
        """
        for dimension in dimensions:
            for metric in dimension.get("dimension_metrics", []):
                if metric.get("metric_id") == metric_id:
                    metric["metric_metadata"] = result
                    return


__all__ = ["EvaluatorOrchestrator"]
