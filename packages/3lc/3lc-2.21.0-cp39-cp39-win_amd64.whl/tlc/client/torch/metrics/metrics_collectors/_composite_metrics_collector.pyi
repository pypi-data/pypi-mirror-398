from _typeshed import Incomplete
from tlc.client.torch.metrics.metrics_collectors import MetricsCollectorType as MetricsCollectorType
from tlc.client.torch.metrics.metrics_collectors.functional_metrics_collector import FunctionalMetricsCollector as FunctionalMetricsCollector
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.schema import Schema as Schema

logger: Incomplete

class _CompositeMetricsCollector(MetricsCollector):
    """A metrics collector that combines the results of multiple metrics collectors.

    Internal class used to simplify the implementation of combining metrics from multiple metrics collectors.

    Allows for unified exception handling and logging when using multiple metrics collectors.
    """
    metrics_collectors: Incomplete
    def __init__(self, metrics_collectors: MetricsCollectorType, compute_aggregates: bool = True) -> None: ...
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]: ...
    def reset(self) -> None:
        """Resets the metrics collectors."""
    @property
    def column_schemas(self) -> dict[str, Schema]:
        """Gets the column schemas of the metrics collector."""
    @property
    def aggregate_values(self) -> dict[str, float]:
        """Gets the aggregate values of the metrics collector."""
