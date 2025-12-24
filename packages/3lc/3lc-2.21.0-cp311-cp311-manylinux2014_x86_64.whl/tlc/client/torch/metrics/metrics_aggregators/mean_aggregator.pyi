from _typeshed import Incomplete
from tlc.client.torch.metrics.metrics_aggregators.aggregator import Aggregator as Aggregator
from tlc.core.schema import ScalarValue as ScalarValue, Schema as Schema
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from typing import Any

logger: Incomplete

class MeanAggregator(Aggregator):
    """An aggregator that computes the mean any computable sub-value contained in a column in a metric batch."""
    SUFFIX: str
    SEPARATOR: str
    def compute_batch_aggregate(self, computed_metrics: dict[str, list[Any]]) -> dict[str, Any]:
        """
        Computes aggregate metrics for a single batch.

        This overridden method computes mean metrics for each column and collects them into a dictionary.
        For nested or composite columns, the mean is computed recursively by traversing each sub-column.

        :param computed_metrics: A dictionary where the keys are column names and the values are lists of metrics.

        :returns: A dictionary containing the mean value(s) for each computable column.
        """
    def aggregate_across_batches(self) -> dict[str, Any]:
        """Aggregates mean metrics across all batches.

        After all batches have been processed, this method calculates the global mean for each column by averaging the
        batch-wise means.

        :returns: A dictionary containing the global mean value(s) for each computable column.
        """
