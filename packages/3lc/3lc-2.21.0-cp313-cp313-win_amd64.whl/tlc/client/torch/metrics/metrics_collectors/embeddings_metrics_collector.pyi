import torch
from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.constants.column_names import EMBEDDING_COL_NAME as EMBEDDING_COL_NAME
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_NN_EMBEDDING as NUMBER_ROLE_NN_EMBEDDING
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Schema as Schema
from typing import Callable, Literal

logger: Incomplete

class EmbeddingsMetricsCollector(MetricsCollector):
    '''Metrics collector that prepares hidden layer activations for storage.

    Assumes that the provided `predictor_output` contains a dictionary of hidden layers, where the keys are the layer
    indices and the values are the activations of the layer.

    Returns metrics batches with a column named "embeddings_{layer}" for each layer provided.

    The activations of intermediate modules can have arbitrary shape, and in order to write them to a Table, they must
    be reshaped to 1D arrays (flattened).

    Will ensure all layers are flattened according to `reshape_strategy[layer]`.
    '''
    def __init__(self, layers: Sequence[int], reshape_strategy: dict[int, Literal['mean', 'flatten', 'avg_pool_1_1', 'avg_pool_2_2', 'avg_pool_3_3']] | dict[int, Callable[[torch.Tensor], torch.Tensor]] | dict[int, tuple[Callable[[torch.Tensor], torch.Tensor], str]] | None = None) -> None:
        '''Create a new embeddings metrics collector.

        :param layers: The layers to collect embeddings from. All layers must be present in the hidden layers returned
            by the {py:class}`Predictor<tlc.client.torch.metrics.predictor.Predictor>`. In practice this means that the
            `Predictor` used during metrics collection must be created with the `layers` argument set to a superset of
            the layers provided here.
        :param reshape_strategy: The reshaping strategy to use for each layer. Hidden layer activations can have
            arbitrary shapes, and in order to be written to a Table, they must be reshaped to 1D arrays. Can be either
            "mean", which takes the mean across all non-first dimensions (excluding batch dimension), or "flatten",
            which flattens all dimensions after the batch dimension, or "avg_pool_1_1", "avg_pool_2_2", or
            "avg_pool_3_3", which use average pooling and a given output size to ensure consistent shapes.  When using
            the "flatten" strategy, the inputs to the model should have the same shape across batches. Otherwise, use
            the "mean" strategy, or one of the average pooling strategies instead. It is also possible to provide a
            callable which performs the flattening. (Default: "mean" for all layers)
        '''
    def compute_metrics(self, _1: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]:
        """Collect and flatten hidden layer activations from model outputs.

        :param predictor_output: The outputs from a {class}`Predictor<tlc.client.torch.metrics.Predictor>`.
        :returns: A dictionary of column names to batch of flattened embeddings.
        """
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
