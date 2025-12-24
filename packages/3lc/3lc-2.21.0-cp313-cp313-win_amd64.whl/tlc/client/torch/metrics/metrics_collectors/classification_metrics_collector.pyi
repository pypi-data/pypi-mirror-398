import torch
from _typeshed import Incomplete
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.schema import Float32Value as Float32Value, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema
from typing import Callable

class ClassificationMetricsCollector(MetricsCollector):
    """Collect common metrics for classification tasks.

    This class is a specialized version of `MetricsCollector` and is designed to collect metrics relevant to
    classification problems. It is assumed that the result of the forward pass of the model is the raw logits
    for each class.

    - `loss`: The per-sample loss value, computed with the provided criterion function. By default, this is the
        cross-entropy loss.
    - `predicted`: The predicted class label.
    - `accuracy`: The per-sample accuracy of the prediction, i.e. whether it is correct.
    - `confidence`: The confidence of the prediction.

    :Example:

    ```python
    table = ...
    model = ...
    collector = ClassificationMetricsCollector()

    tlc.collect_metrics(table, collector, model)
    ```
    """
    classes: Incomplete
    loss_fn: Incomplete
    predicted_schema: Incomplete
    def __init__(self, classes: list[str] | None = None, loss_fn: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] = ..., compute_aggregates: bool = True, preprocess_fn: Callable[[SampleData, PredictorOutput], tuple[SampleData, torch.Tensor]] | None = None) -> None:
        '''Initialize the classification metrics collector

        :param classes: List of class names. If provided, the predicted schema will be updated to include a value map.
        :param loss_fn: Unreduced (per-sample) loss function to use for calculating the loss metric. Default is
            `torch.nn.CrossEntropyLoss(reduction="none")`.
        :param compute_aggregates: Whether to compute aggregate metrics. Default is `True`.
        :param preprocess_fn: Function to preprocess the batch and predictor output.
        '''
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]: ...
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
    def preprocess(self, batch: SampleData, predictor_output: PredictorOutput) -> tuple[SampleData, torch.Tensor]: ...
    def is_one_hot(self, labels: torch.Tensor) -> bool:
        """Check if labels are one-hot encoded."""
