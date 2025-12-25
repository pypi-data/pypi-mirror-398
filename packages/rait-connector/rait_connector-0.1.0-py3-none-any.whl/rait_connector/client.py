"""Main client interface for RAIT Connector."""

import base64
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import requests
from azure.ai.evaluation import AzureOpenAIModelConfiguration
from azure.identity import DefaultAzureCredential

from .auth import AuthenticationService
from .config import settings
from .encryption import Encryptor
from .evaluators import EvaluatorOrchestrator
from .exceptions import EncryptionError, EvaluationError, MetricsError
from .http import HttpSessionFactory
from .models import EvaluationInput

logger = logging.getLogger(__name__)


class RAITClient:
    """Main client for interacting with RAIT API and performing evaluations.

    This client handles:
    - Authentication with RAIT API
    - Fetching enabled metrics configuration
    - Running metric evaluations (sequential or parallel)
    - Encrypting and posting results to API

    Example:
        >>> client = RAITClient()
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

    def __init__(
        self,
        rait_api_url: Optional[str] = None,
        rait_client_id: Optional[str] = None,
        rait_client_secret: Optional[str] = None,
        azure_client_id: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
        azure_client_secret: Optional[str] = None,
        azure_openai_endpoint: Optional[str] = None,
        azure_openai_api_key: Optional[str] = None,
        azure_openai_deployment: Optional[str] = None,
        azure_openai_api_version: Optional[str] = None,
        azure_subscription_id: Optional[str] = None,
        azure_resource_group: Optional[str] = None,
        azure_project_name: Optional[str] = None,
        azure_account_name: Optional[str] = None,
        azure_ai_project_url: Optional[str] = None,
    ):
        """Initialize RAIT client.

        Args:
            rait_api_url: RAIT API endpoint URL
            rait_client_id: RAIT client ID
            rait_client_secret: RAIT client secret
            azure_client_id: Azure AD client ID
            azure_tenant_id: Azure AD tenant ID
            azure_client_secret: Azure AD client secret
            azure_openai_endpoint: Azure OpenAI endpoint
            azure_openai_api_key: Azure OpenAI API key
            azure_openai_deployment: Azure OpenAI deployment name
            azure_openai_api_version: Azure OpenAI API version
            azure_subscription_id: Azure subscription ID
            azure_resource_group: Azure resource group name
            azure_project_name: Azure AI project name
            azure_account_name: Azure account name
            azure_ai_project_url: Azure AI project URL
        """
        self.settings = settings.merge_with(
            rait_api_url=rait_api_url,
            rait_client_id=rait_client_id,
            rait_client_secret=rait_client_secret,
            azure_client_id=azure_client_id,
            azure_tenant_id=azure_tenant_id,
            azure_client_secret=azure_client_secret,
            azure_openai_endpoint=azure_openai_endpoint,
            azure_openai_api_key=azure_openai_api_key,
            azure_openai_deployment=azure_openai_deployment,
            azure_openai_api_version=azure_openai_api_version,
            azure_subscription_id=azure_subscription_id,
            azure_resource_group=azure_resource_group,
            azure_project_name=azure_project_name,
            azure_account_name=azure_account_name,
            azure_ai_project_url=azure_ai_project_url,
        )

        self._session = HttpSessionFactory.get_default_session()

        self._auth_service = AuthenticationService(
            api_url=self.settings.rait_api_url,
            client_id=self.settings.rait_client_id,
            client_secret=self.settings.rait_client_secret,
        )

        self._model_config: Optional[AzureOpenAIModelConfiguration] = None
        self._azure_ai_project: Optional[Dict[str, str]] = None
        self._credential: Optional[DefaultAzureCredential] = None
        self._encryptor: Optional[Encryptor] = None
        self._enabled_metrics: Optional[List[Dict[str, Any]]] = None

        logger.info("RAIT Client initialized")

    def _get_model_config(self) -> AzureOpenAIModelConfiguration:
        """Get or create Azure OpenAI model configuration.

        Returns:
            Azure OpenAI model configuration
        """
        if self._model_config is None:
            self._model_config = AzureOpenAIModelConfiguration(
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_key=self.settings.azure_openai_api_key,
                azure_deployment=self.settings.azure_openai_deployment,
                api_version=self.settings.azure_openai_api_version,
            )
            logger.debug("Created Azure OpenAI model configuration")
        return self._model_config

    def _get_azure_ai_project(self) -> Union[str, Dict[str, str]]:
        """Get Azure AI project configuration.

        Returns:
            Azure AI project URL string or configuration dict
        """
        if self._azure_ai_project is None:
            self._azure_ai_project = self.settings.get_azure_ai_project_dict()
            logger.debug("Created Azure AI project configuration")
        return self.settings.azure_ai_project_url or self._azure_ai_project

    def _get_credential(self) -> DefaultAzureCredential:
        """Get or create Azure credential.

        Returns:
            Azure credential
        """
        if self._credential is None:
            self._credential = DefaultAzureCredential()
            logger.debug("Created Azure credential")
        return self._credential

    def _get_encryptor(self) -> Encryptor:
        """Get or create encryptor with public key from API.

        Returns:
            Encryptor instance

        Raises:
            EncryptionError: If public key retrieval fails
        """
        if self._encryptor is None:
            try:
                headers = self._auth_service.get_auth_headers()

                response = self._session.get(
                    f"{self.settings.rait_api_url}/api/model-registry/public-key/",
                    headers=headers,
                    timeout=30,
                )
                response.raise_for_status()

                data = response.json()
                public_key = data.get("data", {}).get("public_key")

                if not public_key:
                    raise EncryptionError("Public key missing from API response")

                self._encryptor = Encryptor(public_key=public_key)
                logger.info("Encryption key retrieved and encryptor initialized")

            except requests.RequestException as e:
                raise EncryptionError(f"Failed to fetch encryption key: {e}") from e

        return self._encryptor

    def get_enabled_metrics(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Fetch enabled metrics configuration from API.

        Args:
            force_refresh: If True, bypass cache and fetch from API

        Returns:
            List of ethical dimensions with their metrics

        Raises:
            MetricsError: If API call fails
        """
        if self._enabled_metrics is not None and not force_refresh:
            return self._enabled_metrics

        logger.info("Fetching enabled metrics from API")

        try:
            headers = self._auth_service.get_auth_headers()

            response = self._session.get(
                f"{self.settings.rait_api_url}/api/model-registry/enabled-metrics/",
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            data = response.json()
            metrics_config = data.get("data", [])

            if not isinstance(metrics_config, list):
                raise MetricsError("Invalid metrics configuration format")

            self._enabled_metrics = metrics_config

            total_dimensions = len(metrics_config)
            total_metrics = sum(
                len(dim.get("dimension_metrics", [])) for dim in metrics_config
            )

            logger.info(
                f"Retrieved {total_dimensions} dimensions with {total_metrics} metrics"
            )

            return metrics_config

        except requests.HTTPError as e:
            raise MetricsError(
                f"HTTP error fetching metrics: {e.response.status_code}"
            ) from e
        except requests.RequestException as e:
            raise MetricsError(f"Network error fetching metrics: {e}") from e
        except Exception as e:
            raise MetricsError(f"Unexpected error fetching metrics: {e}") from e

    def evaluate(
        self,
        prompt_id: str,
        prompt_url: str,
        timestamp: str,
        model_name: str,
        model_version: str,
        query: str,
        response: str,
        environment: str,
        purpose: str,
        ground_truth: str = "",
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        parallel: bool = True,
        max_workers: int = 5,
        fail_fast: bool = False,
        connector_logs: str = "",
    ) -> Dict[str, Any]:
        """Evaluate a single prompt and automatically post results to API.

        Args:
            prompt_id: Unique identifier for the prompt
            prompt_url: URL reference to the prompt
            timestamp: ISO 8601 timestamp
            model_name: Name of the LLM model
            model_version: Version of the LLM model
            query: User's input query
            response: LLM's generated response
            environment: Execution environment
            purpose: Evaluation purpose
            ground_truth: Expected response (optional)
            context: Additional context (optional)
            metadata: Additional metadata (optional)
            parallel: Whether to run evaluations in parallel
            max_workers: Maximum parallel workers
            fail_fast: Whether to stop on first error
            connector_logs: Optional connector logs to include

        Returns:
            Dict containing prompt data and post response

        Raises:
            EvaluationError: If evaluation fails
            MetricsError: If posting fails
        """
        logger.info(f"Evaluating prompt {prompt_id}")

        prompt_data_obj = EvaluationInput(
            prompt_id=prompt_id,
            prompt_url=prompt_url,
            timestamp=timestamp,
            model_name=model_name,
            model_version=model_version,
            query=query,
            response=response,
            ground_truth=ground_truth,
            context=context,
            metadata=metadata or {},
            environment=environment,
            purpose=purpose,
        )

        ethical_dimensions = self.get_enabled_metrics()

        if not ethical_dimensions:
            logger.warning("No enabled metrics found")
            ethical_dimensions = []

        orchestrator = EvaluatorOrchestrator(
            model_config=self._get_model_config(),
            azure_ai_project=self._get_azure_ai_project(),
            credential=self._get_credential(),
        )

        eval_data = {
            "query": query,
            "response": response,
            "context": context,
            "ground_truth": ground_truth,
        }

        try:
            evaluated_dimensions = orchestrator.evaluate_metrics(
                prompt_data=eval_data,
                ethical_dimensions=ethical_dimensions,
                parallel=parallel,
                max_workers=max_workers,
                fail_fast=fail_fast,
            )

            print(evaluated_dimensions)

            logger.info(f"Evaluation completed for prompt {prompt_id}")

        except Exception as e:
            raise EvaluationError(
                f"Evaluation failed for prompt {prompt_id}: {e}"
            ) from e

        evaluation_result = {
            "prompt_id": prompt_id,
            "prompt_url": prompt_url,
            "model_name": model_name,
            "model_version": model_version,
            "environment": environment,
            "purpose": purpose,
            "ethical_dimensions": evaluated_dimensions,
        }

        post_response = self._post_evaluation(evaluation_result, connector_logs)

        return {
            **prompt_data_obj.model_dump(),
            "ethical_dimensions": evaluated_dimensions,
            "post_response": post_response,
        }

    def _post_evaluation(
        self,
        evaluation_result: Dict[str, Any],
        connector_logs: str = "",
    ) -> Dict[str, Any]:
        """Internal method to post evaluation results to RAIT API.

        Args:
            evaluation_result: Result from evaluation
            connector_logs: Optional connector logs to include

        Returns:
            Dict with status code and response text

        Raises:
            MetricsError: If posting fails
        """
        logger.info(f"Posting evaluation for prompt {evaluation_result['prompt_id']}")

        try:
            encryptor = self._get_encryptor()

            model_data_logs = {
                "prompt_id": evaluation_result["prompt_id"],
                "prompt_url": evaluation_result["prompt_url"],
                "ethical_dimensions": evaluation_result["ethical_dimensions"],
            }

            encrypted_model_data = encryptor.encrypt(
                json.dumps(model_data_logs, ensure_ascii=False)
            )
            encrypted_model_data_b64 = base64.b64encode(encrypted_model_data).decode(
                "utf-8"
            )

            encrypted_logs = encryptor.encrypt(connector_logs)
            encrypted_logs_b64 = base64.b64encode(encrypted_logs).decode("utf-8")

            payload = {
                "model_name": evaluation_result["model_name"],
                "model_version": evaluation_result["model_version"],
                "model_environment": evaluation_result["environment"],
                "model_purpose": evaluation_result["purpose"],
                "created_at": datetime.now().isoformat(),
                "model_data_logs": encrypted_model_data_b64,
                "connector_logs": encrypted_logs_b64,
            }

            headers = self._auth_service.get_auth_headers()

            response = self._session.post(
                f"{self.settings.rait_api_url}/api/model-registry/model-data-logs/",
                json=payload,
                headers=headers,
                timeout=30,
            )
            response.raise_for_status()

            logger.info(
                f"Successfully posted evaluation (status={response.status_code})"
            )

            return {
                "status_code": response.status_code,
                "response": response.text,
            }

        except requests.HTTPError as e:
            raise MetricsError(
                f"HTTP error posting metrics: {e.response.status_code}"
            ) from e
        except requests.RequestException as e:
            raise MetricsError(f"Network error posting metrics: {e}") from e
        except Exception as e:
            raise MetricsError(f"Unexpected error posting metrics: {e}") from e

    def evaluate_batch(
        self,
        prompts: List[Union[Dict[str, Any], EvaluationInput]],
        parallel: bool = True,
        max_workers: int = 5,
        fail_fast: bool = False,
        connector_logs: str = "",
        on_complete: Optional[callable] = None,
    ) -> Dict[str, Any]:
        """Evaluate multiple prompts.

        Args:
            prompts: List of prompt data (dicts or EvaluationInput objects)
            parallel: Whether to run evaluations in parallel
            max_workers: Maximum parallel workers
            fail_fast: Whether to stop on first error
            connector_logs: Optional connector logs to include
            on_complete: Optional callback function called after all evaluations complete.
                        Receives a dict with results, errors, and summary statistics.

        Returns:
            Dict with results, errors, and summary statistics

        Example:
            >>> def my_callback(summary):
            ...     print(f"Completed: {summary['successful']}/{summary['total']}")
            ...     for result in summary['results']:
            ...         print(f"  - {result['prompt_id']}")
            >>>
            >>> client.evaluate_batch(prompts, on_complete=my_callback)
        """
        logger.info(f"Starting batch evaluation of {len(prompts)} prompts")

        results = []
        errors = []

        for prompt in prompts:
            if isinstance(prompt, dict):
                prompt_kwargs = prompt
            else:
                prompt_kwargs = prompt.model_dump()

            try:
                result = self.evaluate(
                    **prompt_kwargs,
                    parallel=parallel,
                    max_workers=max_workers,
                    fail_fast=fail_fast,
                    connector_logs=connector_logs,
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Failed to evaluate prompt: {e}")
                errors.append(
                    {
                        "prompt_id": prompt_kwargs.get("prompt_id"),
                        "error": str(e),
                    }
                )

                if fail_fast:
                    raise EvaluationError(f"Batch evaluation failed: {e}") from e

        summary = {
            "results": results,
            "errors": errors,
            "total": len(prompts),
            "successful": len(results),
            "failed": len(errors),
        }

        if on_complete:
            try:
                on_complete(summary)
            except Exception as callback_error:
                logger.error(f"Callback error: {callback_error}")

        return summary


__all__ = ["RAITClient"]
