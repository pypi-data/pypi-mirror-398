import abc
from _typeshed import Incomplete
from abc import abstractmethod
from tlc.client.torch.metrics.metrics_aggregators import MeanAggregator as MeanAggregator
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.schema import Schema as Schema
from typing import Any, Callable, final

logger: Incomplete

class MetricsCollector(metaclass=abc.ABCMeta):
    '''Base class for all metrics collectors.

    A MetricsCollector is a class that computes metrics from a batch of data together with corresponding predictor
    output, usually the result of passing the batch through a model.

    Custom metrics collectors can be created by subclassing this class and implementing the {func}`compute_metrics`, and
    optionally overriding the {func}`column_schemas` property.

    A simpler way to create a custom metrics collector is to use the
    {class}`FunctionalMetricsCollector<tlc.client.torch.metrics.metrics_collectors.functional_metrics_collector.FunctionalMetricsCollector>`
    class, which takes a function that computes the metrics as input.

    Several pre-built metrics collectors are provided in the
    {class}`metrics_collectors<tlc.client.torch.metrics.metrics_collectors>` module.


    :Example:

    ```python
    table = ...
    model = timm.create_model("resnet18", pretrained=False)

    mc1 = tlc.ClassificationMetricsCollector()
    mc2 = tlc.EmbeddingMetricsCollector()
    mc3 = lambda batch, predictor_output: {"metric": [...]}

    predictor = tlc.Predictor(model, layers=[99])

    tlc.collect_metrics(table, [mc1, mc2, mc3], predictor)
    ```
    '''
    def __init__(self, preprocess_fn: Callable[[SampleData, PredictorOutput], tuple[Any, Any]] | None = None, compute_aggregates: bool = True) -> None:
        """Create a new metrics collector.

        :param preprocess_fn: A function that pre-processes the batch and predictor output before computing the metrics.
        :param compute_aggregates: Whether to compute aggregates for the metrics.
        """
    @final
    def __call__(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]: ...
    @abstractmethod
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]:
        """Compute metrics from a batch of data and corresponding predictor output.

        Subclasses should implement this method to compute the metrics.

        :param batch: The batch of data.
        :param predictor_output: The predictor output.
        :returns: A dictionary of metrics.
        """
    def preprocess(self, batch: SampleData, predictor_output: PredictorOutput) -> tuple[Any, Any]:
        """Pre-process the batch and predictor output before computing the metrics.

        Calls the provided pre-process function if one is provided, otherwise returns the batch and predictor output
        unchanged.
        """
    def reset(self) -> None: ...
    @property
    def aggregate_values(self) -> dict[str, float]: ...
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
MetricsCollectorCallableType = Callable[[SampleData, PredictorOutput], dict[str, MetricData]]
MetricsCollectorType = list[MetricsCollector] | MetricsCollector | list[MetricsCollectorCallableType] | MetricsCollectorCallableType
