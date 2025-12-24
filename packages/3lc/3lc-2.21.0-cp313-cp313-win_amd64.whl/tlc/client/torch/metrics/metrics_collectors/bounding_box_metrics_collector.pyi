from _typeshed import Incomplete
from tlc.client.sample_type import CategoricalLabel as CategoricalLabel, InstanceSegmentationMasks as InstanceSegmentationMasks
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import PredictorOutput as PredictorOutput
from tlc.core.builtins.constants.column_names import BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, FALSE_NEGATIVE as FALSE_NEGATIVE, FALSE_POSITIVE as FALSE_POSITIVE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, INSTANCE_PROPERTIES as INSTANCE_PROPERTIES, IOU as IOU, LABEL as LABEL, MASKS as MASKS, PREDICTED_BOUNDING_BOXES as PREDICTED_BOUNDING_BOXES, PREDICTED_SEGMENTATIONS as PREDICTED_SEGMENTATIONS, TRUE_POSITIVE as TRUE_POSITIVE
from tlc.core.builtins.constants.display_importances import DISPLAY_IMPORTANCE_PREDICTED_BOUNDING_BOX as DISPLAY_IMPORTANCE_PREDICTED_BOUNDING_BOX
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_MIN_X as NUMBER_ROLE_BB_MIN_X, NUMBER_ROLE_BB_MIN_Y as NUMBER_ROLE_BB_MIN_Y, NUMBER_ROLE_BB_SIZE_X as NUMBER_ROLE_BB_SIZE_X, NUMBER_ROLE_BB_SIZE_Y as NUMBER_ROLE_BB_SIZE_Y
from tlc.core.builtins.schemas import BoundingBoxListSchema as BoundingBoxListSchema
from tlc.core.builtins.types import MetricData as MetricData, SampleData as SampleData
from tlc.core.helpers.segmentation_helper import SegmentationHelper as SegmentationHelper
from tlc.core.schema import Int32Value as Int32Value, MapElement as MapElement, ScalarValue as ScalarValue, Schema as Schema
from tlc.core.type_helper import TypeHelper as TypeHelper
from typing import Any, Callable, TypedDict

logger: Incomplete

class COCOAnnotation(TypedDict):
    """A single ground truth annotation in the COCO format.

    Corresponds to the official COCO annotation format: https://cocodataset.org/#format-data
    """
    category_id: int
    score: float | None
    bbox: list[float]
    image_id: int | None
    segmentation: Any | None

class COCOGroundTruth(TypedDict):
    """A single ground truth annotation in the COCO format.

    Corresponds to the official COCO annotation format: https://cocodataset.org/#format-data
    """
    image_id: int | None
    annotations: list[COCOAnnotation]
    height: int | None
    width: int | None

class COCOPrediction(TypedDict):
    """A single prediction in the COCO results format."""
    annotations: list[COCOAnnotation]

class _TLCPredictedBoundingBox(TypedDict):
    """A bounding box in a format compatible with the 3LC Dashboard."""
    x0: float
    y0: float
    x1: float
    y1: float
    label: int
    confidence: float | None
    iou: float | None

class _TLCPredictedBoundingBoxes(TypedDict):
    """A list of bounding boxes in a format compatible with the 3LC Dashboard."""
    bb_list: list[_TLCPredictedBoundingBox]
    image_width: int | None
    image_height: int | None

class BoundingBoxMetricsCollector(MetricsCollector):
    '''Compute metrics for bounding box predictions.

    By default, this metrics collector only collects the predicted bounding boxes and per-bounding box metrics (label,
    iou, confidence).

    If `compute_derived_metrics` is `True`, the additional metrics `tp`, `fp`, and `fn` will be computed according to
    the `derived_metrics_mode` flag. If this flag is set to "strict", then only one predicted bounding box can match
    each ground truth bounding box. If this flag is set to "relaxed", then multiple predicted bounding boxes can match
    each ground truth bounding box. When multiple boxes match the same ground truth box, only one true positive is
    counted.

    For working with different sample/prediction formats, the `preprocess_fn` argument can be used to provide a custom
    preprocessing function. This function should take a batch of samples and predictions and return a tuple of lists of
    [COCOGroundTruth](#tlc.client.torch.metrics.metrics_collectors.bounding_box_metrics_collector.COCOGroundTruth) and
    [COCOPrediction](#tlc.client.torch.metrics.metrics_collectors.bounding_box_metrics_collector.COCOPrediction)
    respectively.

    For computing additional metrics, the `extra_metrics_fn` argument can be provided to add additional metrics or
    update already collected metrics.

    :param model: The model to be used in the prediction pass.
    :param classes: A list of class names.
    :param label_mapping: A dictionary mapping class indices to the range [0, num_classes). Class indices in the source
        dataset could be in any range, so this mapping is used to convert them to the range [0, num_classes), which is
        usually used in object detection models.
    :param iou_threshold: The IoU threshold to use for matching predictions to ground truths.
    :param compute_derived_metrics: Whether to compute derived metrics.
    :param derived_metrics_mode: The mode to use when computing derived metrics. Must be one of "strict" or "relaxed".
    :param extra_metrics_fn: A function that takes a batch of samples, a batch of predictions, and a dictionary of
        computed metrics. This function can add additional metrics to the metrics collected by the metrics collector,
        modify existing metrics, or delete metrics. Any such changes should be accompanied by a schema override, see
        {func}`add_schema()<BoundingBoxMetricsCollector.add_schema>`,
        {func}`update_schema()<BoundingBoxMetricsCollector.update_schema>`, and
        {func}`delete_schema()<BoundingBoxMetricsCollector.delete_schema>` for details.
    :param preprocess_fn: A function that takes a batch of samples and a batch of predictions and returns modified lists
        in a standard format, compatible with this metrics collector.
    '''
    classes: Incomplete
    label_mapping: Incomplete
    inverse_label_mapping: Incomplete
    extra_metrics_fn: Incomplete
    compute_derived_metrics: Incomplete
    iou_threshold: Incomplete
    derived_metrics_mode: Incomplete
    save_segmentations: Incomplete
    def __init__(self, classes: list[str], label_mapping: dict[int, int], iou_threshold: float = 0.5, compute_derived_metrics: bool = False, derived_metrics_mode: str = 'relaxed', extra_metrics_fn: Callable[[list[COCOGroundTruth], list[COCOPrediction], dict[str, list[Any]] | None], None] | None = None, preprocess_fn: Callable[[SampleData, PredictorOutput], tuple[list[COCOGroundTruth], list[COCOPrediction]]] | None = None, compute_aggregates: bool = True, save_segmentations: bool = False) -> None: ...
    def compute_metrics(self, batch: SampleData, predictor_output: PredictorOutput) -> dict[str, MetricData]:
        """Compute metrics for bounding box predictions.

        :param batch: A batch of samples.
        :param predictions: A batch of predictions.

        :returns: A dictionary of mapping metric names to metric values for a batch of inputs.
        """
    @staticmethod
    def check_schema_compatibility(metrics: dict[str, list[Any]], column_schemas: dict[str, Schema]) -> None:
        """Check that the metrics are compatible with the column schemas."""
    def preprocess(self, batch: SampleData, predictor_output: PredictorOutput) -> tuple[list[COCOGroundTruth], list[COCOPrediction]]:
        """Default preprocessor for the raw batch and predictor output.

        This preprocessor recognizes and transforms detectron2 samples/predictions, otherwise it assumes that the
        samples/predictions are already in the COCO format.

        :param batch: A batch of samples.
        :param predictor_output: A batch of predictions.

        :returns: A tuple containing the preprocessed batch and predictions.
        """
    @property
    def column_schemas(self) -> dict[str, Schema]: ...
    def add_schema(self, key: str, schema: Schema) -> None:
        '''Add a schema.

        When adding new values to the metrics computed by this metrics collector, the schemas for the new values should
        also be added.

        :Example:

        ```python
        # assuming `extra_metrics_fn` adds a new top-level metric called "my_metric", and adds a new per-
        # bounding box metric called "bb_area".

        bbox_metrics_collector.add_schema("my_metric", Schema(value=Int32Value()))
        bbox_metrics_collector.add_schema("bbs_predicted.bb_list.bb_area", Schema(value=Float32Value()))
        ```

        :param key: The key of the schema to add. Nested schemas can be added by using the dot notation.
        :param schema: The schema to add, may be nested.
        '''
    def update_schema(self, key: str, schema: Schema) -> None:
        '''Update a schema.

        When updating metrics-values computed by this metrics collector, the schemas for the updated values should also
        be updated.

        :Example:

        ```python
        # assuming `extra_metrics_fn` modifies the top-level metric `TRUE_POSITIVE`, and modifies the per-
        # bounding box metric `iou`.

        bbox_metrics_collector.update_schema(
            "tp",
            Schema(value=Float32Value(), description="This metric used to be an int, but now it is a float."),
        )
        bbox_metrics_collector.update_schema(
            "bbs_predicted.bb_list.iou",
            Schema(value=Float32Value(), description="I have changed the description of this metric."),
        )
        ```

        :param key: The key of the schema to modify. Nested schemas can be modified by using the dot notation.
        :param schema: The schema to add, may be nested.
        '''
    def delete_schema(self, key: str) -> None:
        '''Delete a schema.

        When deleting metrics-values computed by this metrics collector, the schemas for the deleted values should also
        be deleted.

        :Example:

        ```python
        # assuming `extra_metrics_fn` deletes the top-level metric "FALSE_NEGATIVE", and deletes the per-
        # bounding box metric "iou".

        bbox_metrics_collector.delete_schema("FALSE_NEGATIVE")
        bbox_metrics_collector.delete_schema("bboxes.bounding_boxes.iou")
        ```

        :param key: The key of the schema to delete. Nested schemas can be deleted by using the dot notation.
        '''

def compute_iou(bb1: list[float], bb2: list[float]) -> float:
    """Calculates intersection over union for 2 bounding boxes in XYWH format"""
