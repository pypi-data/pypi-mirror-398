from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.types import SampleData as SampleData
from tlc.core.schema import Schema as Schema
from typing import Any, Callable

class FunctionalMetricsCollector(MetricsCollector):
    """A metrics collector which uses a function to collect metrics."""
    def __init__(self, collection_fn: Callable[[SampleData, PredictorOutput], dict[str, Any]], column_schemas: dict[str, Schema] | None = None, compute_aggregates: bool = True) -> None:
        '''Create a new functional metrics collector.

        :param collection_fn: A function for computing custom metrics. The function should take two arguments: a batch
        of samples, and an instance of {class}`PredictorOutput<tlc.client.torch.metrics.predictor.PredictorOutput>`. It
        should return a dictionary of computed metrics, mapping the names of the metrics to a batch of their values. A
        trivial `collection_fn` might look like this:

        ```python
        def collection_fn(batch, predictor_output):
            return {"prediction": predictor_output.forward}
        ```

        :param column_schemas: A dictionary of schemas for the columns. If no schemas are provided, the schemas will be
            inferred from the column data.
        '''
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, Any]: ...
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
