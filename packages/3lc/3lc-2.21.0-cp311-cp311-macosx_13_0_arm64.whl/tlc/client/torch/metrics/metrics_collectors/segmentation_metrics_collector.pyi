import torch
from PIL import Image
from _typeshed import Incomplete
from tlc.client.sample_type import SegmentationPILImage as SegmentationPILImage
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.constants.column_names import PREDICTED_MASK as PREDICTED_MASK
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.schema import Schema as Schema
from tlc.core.type_helper import TypeHelper as TypeHelper
from typing import Any, Callable

PREDICTED_MASK_METRIC_NAME = PREDICTED_MASK

class SegmentationMetricsCollector(MetricsCollector):
    """Collect predicted masks from model output.

    Predicted masks are converted to PIL images, which can be written to the Run folder by a
    {class}`MetricsTableWriter<tlc.core.writers.metrics_writer.MetricsTableWriter>`.
    """
    label_map: Incomplete
    def __init__(self, label_map: dict[int, str], preprocess_fn: Callable[[SampleData, PredictorOutput], tuple[Any, Any]] | None = None) -> None:
        """Initialize the SegmentationMetricsCollector.

        :param label_map: A dictionary mapping class ids to class labels.
        :param preprocess_fn: A function that pre-processes the model output before computing metrics.
        """
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]:
        """Convert predicted masks from model output to PIL images.

        The result of preprocessing the model output is expected to be a list of tensors.

        :param batch: The input batch (not used).
        :param predictor_output: The output from the Predictor.
        :return: A batch of metrics, where each metric is a PIL image corresponding to a mask.
        """
    def preprocess(self, batch: SampleData, predictor_output: PredictorOutput) -> tuple[SampleData, torch.Tensor]:
        """Default preprocessor for segmentation output.

        By default just forwards the model predictions.

        :param batch: A batch of samples.
        :param predictor_output: A batch of predictions.

        :returns: A tuple containing the preprocessed batch and predictions.
        """
    def tensor_to_pil_image(self, predicted_mask: torch.Tensor) -> Image.Image: ...
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
