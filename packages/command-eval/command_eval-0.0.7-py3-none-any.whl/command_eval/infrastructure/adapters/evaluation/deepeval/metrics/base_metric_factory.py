"""Base metric factory for DeepEval metrics.

Provides common interface and configuration for all metric factories.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from typing import Any


def _import_class(module_path: str, class_name: str) -> type:
    """Import a class from a module path."""
    import importlib
    module = importlib.import_module(module_path)
    cls = getattr(module, class_name, None)
    if cls is None:
        raise ValueError(f"Class '{class_name}' not found in '{module_path}'")
    return cls


def _resolve_env_vars(value: str) -> str:
    """Resolve environment variables in a string.

    Supports ${ENV_VAR} syntax. Returns the original string if no env vars found.
    Returns None if the env var is not set and the entire string is just ${ENV_VAR}.

    Examples:
        "${GEMINI_API_KEY}" -> "actual-api-key" or None if not set
        "prefix-${VAR}-suffix" -> "prefix-value-suffix"
    """
    pattern = r"\$\{([^}]+)\}"

    def replacer(match: re.Match[str]) -> str:
        env_name = match.group(1)
        return os.environ.get(env_name, "")

    # Check if the entire string is just an env var reference
    full_match = re.fullmatch(pattern, value)
    if full_match:
        env_name = full_match.group(1)
        env_value = os.environ.get(env_name)
        # Return None if env var is not set (allows SDK to use its defaults)
        return env_value  # type: ignore[return-value]

    # Otherwise, substitute all env vars in the string
    return re.sub(pattern, replacer, value)


def resolve_instances(value: Any) -> Any:
    """Recursively resolve class_name/class_ref/enum_ref keys and env vars.

    - enum_ref: Returns the enum value (requires module and enum)
    - class_ref: Returns the class itself (requires module)
    - class_name: Instantiates the class with remaining params (requires module)
    - ${ENV_VAR}: Resolves to environment variable value
    """
    if isinstance(value, str):
        if "${" in value:
            return _resolve_env_vars(value)
        return value

    if isinstance(value, dict):
        if "enum_ref" in value:
            enum_ref = value["enum_ref"]
            module_path = value["module"]
            enum_name = value["enum"]
            enum_class = _import_class(module_path, enum_name)
            return getattr(enum_class, enum_ref)

        if "class_ref" in value:
            class_ref = value["class_ref"]
            module_path = value["module"]
            return _import_class(module_path, class_ref)

        if "class_name" in value:
            class_name = value["class_name"]
            module_path = value["module"]
            params = {
                k: resolve_instances(v)
                for k, v in value.items()
                if k not in ("class_name", "module")
            }
            cls = _import_class(module_path, class_name)
            return cls(**params)

        return {k: resolve_instances(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [resolve_instances(item) for item in value]
    else:
        return value


# LLMTestCase parameters - shared between adapter and metric factory
LLM_TEST_CASE_PARAMS: frozenset[str] = frozenset([
    "expected_output",
    "context",
    "retrieval_context",
    "additional_metadata",
    "tools_called",
    "comments",
    "expected_tools",
    "token_cost",
    "completion_time",
    "multimodal",
    "name",
    "tags",
    "mcp_servers",
    "mcp_tools_called",
    "mcp_resources_called",
    "mcp_prompts_called",
])

# LLMTestCase fields that are list type (for file content parsing)
LLM_TEST_CASE_LIST_PARAMS: frozenset[str] = frozenset([
    "context",
    "retrieval_context",
])


class BaseMetricFactory(ABC):
    """Abstract base factory for creating DeepEval metrics.

    Subclasses only need to define:
    - metric_name: The metric identifier
    - metric_class_name: The DeepEval metric class name
    - required_params: Required parameters (optional)
    - unsupported_params: Params to exclude (optional)
    """

    @property
    @abstractmethod
    def metric_name(self) -> str:
        """Get the metric name (e.g., 'answer_relevancy')."""
        pass

    @property
    @abstractmethod
    def metric_class_name(self) -> str:
        """Get the DeepEval metric class name (e.g., 'AnswerRelevancyMetric')."""
        pass

    @property
    def required_params(self) -> frozenset[str]:
        """Get required parameter names. Override if needed."""
        return frozenset()

    @property
    def unsupported_params(self) -> frozenset[str]:
        """Get parameter names to exclude from kwargs. Override if needed."""
        return frozenset()

    @property
    def test_case_params(self) -> frozenset[str]:
        """Parameters that belong to LLMTestCase, not the metric."""
        return LLM_TEST_CASE_PARAMS

    def create(self, params: dict[str, Any], threshold: float) -> Any:
        """Create a metric instance from params.

        Args:
            params: Parameters from YAML (will be resolved automatically).
            threshold: Default threshold value.

        Returns:
            A DeepEval metric instance.
        """
        # Validate required params
        self._validate_required_params(params)

        # Resolve class_name/class_ref/enum_ref
        resolved = resolve_instances(params)

        # Build kwargs
        kwargs = {"threshold": resolved.get("threshold", threshold)}

        # Params to exclude from metric kwargs
        # Note: required_params are never excluded (e.g., GEval's "name" is both
        # a LLMTestCase field and a required metric param)
        excluded_params = (self.unsupported_params | self.test_case_params) - self.required_params

        for key, value in resolved.items():
            # Exclude test_case_params and all *_file params (resolved elsewhere)
            if key not in excluded_params and not key.endswith("_file"):
                kwargs[key] = value

        # Import and instantiate metric class
        metric_class = _import_class("deepeval.metrics", self.metric_class_name)
        return metric_class(**kwargs)

    def _validate_required_params(self, params: dict[str, Any]) -> None:
        """Validate that all required params are present."""
        for param in self.required_params:
            if param not in params:
                raise ValueError(f"{self.metric_class_name} requires '{param}' parameter")


class SimpleMetricFactory(BaseMetricFactory):
    """Data-driven metric factory for simple metrics.

    Use this for metrics that only need metric_name and metric_class_name.
    """

    def __init__(
        self,
        metric_name: str,
        metric_class_name: str,
        required_params: frozenset[str] | None = None,
        unsupported_params: frozenset[str] | None = None,
    ) -> None:
        self._metric_name = metric_name
        self._metric_class_name = metric_class_name
        self._required_params = required_params or frozenset()
        self._unsupported_params = unsupported_params or frozenset()

    @property
    def metric_name(self) -> str:
        return self._metric_name

    @property
    def metric_class_name(self) -> str:
        return self._metric_class_name

    @property
    def required_params(self) -> frozenset[str]:
        return self._required_params

    @property
    def unsupported_params(self) -> frozenset[str]:
        return self._unsupported_params
