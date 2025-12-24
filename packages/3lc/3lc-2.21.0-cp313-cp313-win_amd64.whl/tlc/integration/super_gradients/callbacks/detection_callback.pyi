from .base_callback import MetricsCollectionCallback as MetricsCollectionCallback
from _typeshed import Incomplete
from super_gradients.training.utils.predict.prediction_results import ImageDetectionPrediction, ImagesDetectionPrediction
from tlc.core.builtins.constants.column_names import BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, CONFIDENCE as CONFIDENCE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, LABEL as LABEL, PREDICTED_BOUNDING_BOXES as PREDICTED_BOUNDING_BOXES, X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_MAX_X as NUMBER_ROLE_BB_MAX_X, NUMBER_ROLE_BB_MAX_Y as NUMBER_ROLE_BB_MAX_Y, NUMBER_ROLE_BB_MIN_X as NUMBER_ROLE_BB_MIN_X, NUMBER_ROLE_BB_MIN_Y as NUMBER_ROLE_BB_MIN_Y
from tlc.core.builtins.constants.units import UNIT_ABSOLUTE as UNIT_ABSOLUTE
from tlc.core.builtins.schemas import BoundingBoxListSchema as BoundingBoxListSchema
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema
from typing import Any

logger: Incomplete

class DetectionMetricsCollectionCallback(MetricsCollectionCallback):
    @property
    def label_column_name(self) -> str: ...
    def compute_metrics(self, images: list[str], predictions: ImagesDetectionPrediction | ImageDetectionPrediction, table: Table) -> dict[str, Any]:
        """Compute metrics from a batch of data and corresponding predictions."""
    def metrics_column_schemas(self, table: Table) -> dict[str, Schema]:
        """Return the column schemas for the metrics of this callback."""
