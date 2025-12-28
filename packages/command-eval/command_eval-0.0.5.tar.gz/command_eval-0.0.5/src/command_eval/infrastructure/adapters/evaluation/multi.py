"""Multi-evaluation adapter.

Dispatches evaluation to multiple SDK-specific adapters based on evaluation_specs.
"""

from __future__ import annotations

from command_eval.infrastructure.logging import get_logger

_logger = get_logger(__name__)

from command_eval.domain.ports.evaluation_port import (
    EvaluationConfig,
    EvaluationPort,
    EvaluationResponse,
    EvaluationTestCase,
)
from command_eval.domain.ports.evaluation_port import (
    TestCaseResult as PortTestCaseResult,
)
from command_eval.domain.value_objects.metric_type import MetricType


class MultiEvalAdapter(EvaluationPort):
    """Multi-evaluation adapter that dispatches to SDK-specific adapters.

    This adapter allows registering multiple SDK adapters (deepeval, ragas, custom)
    and dispatches evaluation based on the SDK name in evaluation_specs.

    Example:
        ```python
        multi_adapter = MultiEvalAdapter()
        multi_adapter.register_adapter("deepeval", DeepEvalAdapter())
        multi_adapter.register_adapter("ragas", RagasAdapter())
        multi_adapter.register_adapter("custom", MyCustomAdapter())
        ```
    """

    def __init__(self) -> None:
        """Initialize the multi-evaluation adapter."""
        self._adapters: dict[str, EvaluationPort] = {}

    def register_adapter(self, sdk_name: str, adapter: EvaluationPort) -> None:
        """Register an SDK adapter.

        Args:
            sdk_name: The SDK name (e.g., 'deepeval', 'ragas', 'custom').
            adapter: The adapter implementation.
        """
        self._adapters[sdk_name.lower()] = adapter

    def unregister_adapter(self, sdk_name: str) -> None:
        """Unregister an SDK adapter.

        Args:
            sdk_name: The SDK name to unregister.
        """
        self._adapters.pop(sdk_name.lower(), None)

    def get_adapter(self, sdk_name: str) -> EvaluationPort | None:
        """Get a registered adapter by SDK name.

        Args:
            sdk_name: The SDK name.

        Returns:
            The adapter if registered, None otherwise.
        """
        return self._adapters.get(sdk_name.lower())

    def get_registered_sdks(self) -> frozenset[str]:
        """Get all registered SDK names.

        Returns:
            Frozenset of registered SDK names.
        """
        return frozenset(self._adapters.keys())

    def get_sdk_name(self) -> str:
        """Get the SDK name.

        Returns:
            'multi' as this adapter dispatches to multiple SDKs.
        """
        return "multi"

    def supports_metric(self, metric_type: MetricType) -> bool:
        """Check if any registered adapter supports the metric type.

        Args:
            metric_type: The metric type to check.

        Returns:
            True if any adapter supports the metric.
        """
        return any(
            adapter.supports_metric(metric_type)
            for adapter in self._adapters.values()
        )

    def evaluate(
        self,
        test_cases: list[EvaluationTestCase],
        config: EvaluationConfig,
    ) -> EvaluationResponse:
        """Execute evaluation using appropriate SDK adapters.

        Dispatches test cases to the appropriate SDK adapter based on
        the SDK name in evaluation_specs.

        Args:
            test_cases: List of test cases to evaluate.
            config: Evaluation configuration.

        Returns:
            Combined evaluation response from all adapters.
        """
        _logger.info("MultiEvalAdapter: Starting evaluation")
        _logger.info("  Registered SDKs: %s", list(self._adapters.keys()))
        _logger.info("  Test cases: %d", len(test_cases))

        if not test_cases:
            _logger.info("  No test cases to evaluate")
            return EvaluationResponse.create(tuple(), config.default_threshold)

        # Group test cases by SDK
        sdk_test_cases: dict[str, list[EvaluationTestCase]] = {}
        for tc in test_cases:
            # Get unique SDK names from evaluation_specs
            sdk_names = {spec.sdk.lower() for spec in tc.evaluation_specs}
            _logger.debug("  Test case %s uses SDKs: %s", tc.id, sdk_names)

            # Add test case to each SDK's group
            for sdk_name in sdk_names:
                if sdk_name not in sdk_test_cases:
                    sdk_test_cases[sdk_name] = []
                sdk_test_cases[sdk_name].append(tc)

        # If no evaluation_specs, try to use a default adapter
        if not sdk_test_cases:
            # Try deepeval as default, or first registered adapter
            default_sdk = "deepeval" if "deepeval" in self._adapters else None
            if default_sdk is None and self._adapters:
                default_sdk = next(iter(self._adapters.keys()))

            if default_sdk:
                _logger.info("  Using default SDK: %s", default_sdk)
                sdk_test_cases[default_sdk] = test_cases

        _logger.info("  SDK distribution: %s",
                    {k: len(v) for k, v in sdk_test_cases.items()})

        # Execute evaluation for each SDK
        all_results: dict[str, PortTestCaseResult] = {}

        for sdk_name, cases in sdk_test_cases.items():
            _logger.info("  Evaluating with SDK: %s (%d cases)", sdk_name, len(cases))
            adapter = self._adapters.get(sdk_name)
            if adapter is None:
                _logger.warning("  No adapter registered for SDK: %s", sdk_name)
                # Skip unknown SDKs or create error results
                for tc in cases:
                    if tc.id not in all_results:
                        all_results[tc.id] = PortTestCaseResult(
                            test_case_id=tc.id,
                            metric_results=(),
                        )
                continue

            # Create SDK-specific config (metrics are derived from evaluation_specs)
            sdk_config = EvaluationConfig(
                default_threshold=config.default_threshold,
                verbose_mode=config.verbose_mode,
                options=config.options,
            )

            # Execute evaluation
            _logger.debug("    Calling adapter.evaluate()...")
            response = adapter.evaluate(cases, sdk_config)
            _logger.info("    SDK %s returned %d results", sdk_name, len(response.details))

            # Merge results (combine metric_results from all SDKs)
            for detail in response.details:
                _logger.debug("    Result: %s passed=%s",
                             detail.test_case_id, detail.passed)
                existing = all_results.get(detail.test_case_id)
                if existing is None:
                    all_results[detail.test_case_id] = detail
                else:
                    # Merge metric_results from both
                    merged_metric_results = existing.metric_results + detail.metric_results
                    all_results[detail.test_case_id] = PortTestCaseResult(
                        test_case_id=detail.test_case_id,
                        metric_results=merged_metric_results,
                    )

        # Create final response
        # Order results by original test case order
        ordered_results = [
            all_results[tc.id] for tc in test_cases if tc.id in all_results
        ]

        final_response = EvaluationResponse.create(tuple(ordered_results), config.default_threshold)
        _logger.info("  Final: passed=%d failed=%d",
                    final_response.passed_count,
                    final_response.failed_count)

        return final_response

