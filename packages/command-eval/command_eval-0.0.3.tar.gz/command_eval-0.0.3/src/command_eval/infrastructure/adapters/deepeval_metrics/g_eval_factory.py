"""G-Eval metric factory.

Creates GEval instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.deepeval_metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
)


class GEvalMetricFactory(BaseMetricFactory):
    """Factory for creating GEval metric instances.

    GEval is a customizable metric that uses an LLM to evaluate based on
    user-defined criteria. It's highly flexible and can be adapted for
    various evaluation needs.

    Required LLMTestCase fields depend on evaluation_params configuration.

    Constructor parameters:
        - name (str): Name of the custom metric (required)
        - criteria (str): Description of evaluation aspects (required)
        - evaluation_params (list): LLMTestCaseParams to use (required)
        - evaluation_steps (list[str]): Exact evaluation steps (optional)
        - rubric (list): Score range definitions (optional)
        - threshold (float): Minimum passing threshold (default: 0.5)
        - model (str): Evaluation model (default: 'gpt-4.1')
        - strict_mode (bool): Binary scoring (default: False)
        - async_mode (bool): Concurrent execution (default: True)
        - verbose_mode (bool): Print steps (default: False)
        - evaluation_template: Custom prompt template (optional)
    """

    @property
    def metric_name(self) -> str:
        """Get the metric name.

        Returns:
            'g_eval'
        """
        return "g_eval"

    def create(self, config: MetricConfig) -> Any:
        """Create a GEval metric instance.

        Args:
            config: Metric configuration.
                Must include 'name', 'criteria', and 'evaluation_params'
                in extra_params.

        Returns:
            GEval instance.

        Raises:
            ValueError: If required parameters are missing.
        """
        from deepeval.metrics import GEval

        # Validate required parameters
        if "name" not in config.extra_params:
            raise ValueError("GEval requires 'name' parameter")
        if "criteria" not in config.extra_params:
            raise ValueError("GEval requires 'criteria' parameter")
        if "evaluation_params" not in config.extra_params:
            raise ValueError("GEval requires 'evaluation_params' parameter")

        kwargs = config.to_common_kwargs()

        # Remove include_reason as GEval doesn't use it
        kwargs.pop("include_reason", None)

        # Add required GEval parameters
        kwargs["name"] = config.extra_params["name"]
        kwargs["criteria"] = config.extra_params["criteria"]

        # Convert evaluation_params strings to LLMTestCaseParams enums
        evaluation_params = config.extra_params["evaluation_params"]
        if isinstance(evaluation_params, list):
            from deepeval.test_case import LLMTestCaseParams

            param_mapping = {
                "input": LLMTestCaseParams.INPUT,
                "actual_output": LLMTestCaseParams.ACTUAL_OUTPUT,
                "expected_output": LLMTestCaseParams.EXPECTED_OUTPUT,
                "context": LLMTestCaseParams.CONTEXT,
                "retrieval_context": LLMTestCaseParams.RETRIEVAL_CONTEXT,
            }

            converted_params = []
            for p in evaluation_params:
                if isinstance(p, str) and p.lower() in param_mapping:
                    converted_params.append(param_mapping[p.lower()])
                else:
                    converted_params.append(p)

            kwargs["evaluation_params"] = converted_params
        else:
            kwargs["evaluation_params"] = evaluation_params

        # Handle optional GEval-specific parameters
        if "evaluation_steps" in config.extra_params:
            kwargs["evaluation_steps"] = config.extra_params["evaluation_steps"]

        if "rubric" in config.extra_params:
            kwargs["rubric"] = config.extra_params["rubric"]

        if "evaluation_template" in config.extra_params:
            kwargs["evaluation_template"] = config.extra_params["evaluation_template"]

        return GEval(**kwargs)

    def create_from_params(self, params: dict[str, Any], threshold: float) -> Any:
        """Create a GEval metric from evaluation_spec params.

        For GEval, the params should include:
        - name: Metric name
        - criteria: Evaluation criteria description
        - evaluation_params: List of param names (e.g., ["input", "actual_output"])

        Args:
            params: Parameters from evaluation_spec.
            threshold: Default threshold value.

        Returns:
            GEval instance.
        """
        # Convert evaluation_params strings to LLMTestCaseParams
        if "evaluation_params" in params and isinstance(
            params["evaluation_params"], list
        ):
            from deepeval.test_case import LLMTestCaseParams

            param_mapping = {
                "input": LLMTestCaseParams.INPUT,
                "actual_output": LLMTestCaseParams.ACTUAL_OUTPUT,
                "expected_output": LLMTestCaseParams.EXPECTED_OUTPUT,
                "context": LLMTestCaseParams.CONTEXT,
                "retrieval_context": LLMTestCaseParams.RETRIEVAL_CONTEXT,
            }

            converted_params = []
            for p in params["evaluation_params"]:
                if isinstance(p, str) and p.lower() in param_mapping:
                    converted_params.append(param_mapping[p.lower()])
                else:
                    converted_params.append(p)

            params = {**params, "evaluation_params": converted_params}

        return super().create_from_params(params, threshold)
