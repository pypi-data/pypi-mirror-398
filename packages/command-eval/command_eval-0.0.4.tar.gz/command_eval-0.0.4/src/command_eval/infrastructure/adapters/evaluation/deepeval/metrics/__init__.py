"""DeepEval metric factories.

Each metric has its own factory file for clean separation of concerns.
"""

from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.answer_relevancy_factory import (
    AnswerRelevancyMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.base_metric_factory import (
    BaseMetricFactory,
    MetricConfig,
    RequiredField,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.bias_factory import (
    BiasMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.contextual_precision_factory import (
    ContextualPrecisionMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.contextual_recall_factory import (
    ContextualRecallMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.contextual_relevancy_factory import (
    ContextualRelevancyMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.faithfulness_factory import (
    FaithfulnessMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.g_eval_factory import (
    GEvalMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.hallucination_factory import (
    HallucinationMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.metric_registry import (
    DeepEvalMetricRegistry,
    get_default_registry,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.summarization_factory import (
    SummarizationMetricFactory,
)
from command_eval.infrastructure.adapters.evaluation.deepeval.metrics.toxicity_factory import (
    ToxicityMetricFactory,
)

__all__ = [
    "BaseMetricFactory",
    "MetricConfig",
    "RequiredField",
    "AnswerRelevancyMetricFactory",
    "FaithfulnessMetricFactory",
    "ContextualPrecisionMetricFactory",
    "ContextualRecallMetricFactory",
    "ContextualRelevancyMetricFactory",
    "HallucinationMetricFactory",
    "BiasMetricFactory",
    "ToxicityMetricFactory",
    "SummarizationMetricFactory",
    "GEvalMetricFactory",
    "DeepEvalMetricRegistry",
    "get_default_registry",
]
