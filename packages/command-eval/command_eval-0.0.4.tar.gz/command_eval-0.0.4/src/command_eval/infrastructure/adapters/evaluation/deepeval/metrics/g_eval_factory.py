"""G-Eval metric factory.

Creates GEval instances with proper configuration.
"""

from __future__ import annotations

from typing import Any

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)


class GEvalMetricFactory(BaseMetricFactory):
    """Factory for creating GEval metric instances.

    GEval is a customizable metric that uses an LLM to evaluate based on
    user-defined criteria.

    Required LLMTestCase fields:
        - Depends on evaluation_params configuration

    Constructor parameters (from DeepEval):
        - name (str): Name of the custom metric (REQUIRED)
        - evaluation_params (list): LLMTestCaseParams to use (REQUIRED)
        - criteria (str): Description of evaluation aspects (optional)
        - evaluation_steps (list[str]): Exact evaluation steps (optional)
        - rubric (list): Score range definitions (optional)
        - threshold (float): Minimum passing threshold (default: 0.5)
        - top_logprobs (int): Number of top logprobs (default: 20)
        - model (str): Evaluation model (optional)
        - async_mode (bool): Concurrent execution (default: True)
        - strict_mode (bool): Binary scoring (default: False)
        - verbose_mode (bool): Print steps (default: False)
        - evaluation_template: Custom template class (optional)
    """

    @property
    def metric_name(self) -> str:
        return "g_eval"

    @property
    def required_fields(self) -> frozenset[RequiredField]:
        return frozenset()

    def create(self, config: MetricConfig) -> Any:
        from deepeval.metrics import GEval

        extra = config.extra_params

        if "name" not in extra:
            raise ValueError("GEval requires 'name' parameter")
        if "evaluation_params" not in extra:
            raise ValueError("GEval requires 'evaluation_params' parameter")

        kwargs = config.to_common_kwargs()
        kwargs.pop("include_reason", None)

        kwargs["name"] = extra["name"]
        kwargs["evaluation_params"] = self._convert_evaluation_params(
            extra["evaluation_params"]
        )

        for key in ("criteria", "evaluation_steps", "rubric", "evaluation_template", "top_logprobs"):
            if key in extra:
                kwargs[key] = extra[key]

        return GEval(**kwargs)

    def _convert_evaluation_params(self, params: Any) -> list[Any]:
        """Convert string param names to LLMTestCaseParams enums."""
        if not isinstance(params, list):
            return params

        from deepeval.test_case import LLMTestCaseParams

        mapping = {
            "input": LLMTestCaseParams.INPUT,
            "actual_output": LLMTestCaseParams.ACTUAL_OUTPUT,
            "expected_output": LLMTestCaseParams.EXPECTED_OUTPUT,
            "context": LLMTestCaseParams.CONTEXT,
            "retrieval_context": LLMTestCaseParams.RETRIEVAL_CONTEXT,
        }

        return [
            mapping.get(p.lower(), p) if isinstance(p, str) else p
            for p in params
        ]
