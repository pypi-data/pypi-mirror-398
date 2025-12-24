from .base_callback import MetricsCollectionCallback as MetricsCollectionCallback
from super_gradients.training.utils.predict.prediction_pose_estimation_results import ImagePoseEstimationPrediction, ImagesPoseEstimationPrediction
from tlc.core.builtins.constants.column_names import INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, KEYPOINTS_2D as KEYPOINTS_2D, LABEL as LABEL
from tlc.core.builtins.schemas.geometries import Keypoints2DSchema as Keypoints2DSchema
from tlc.core.data_formats.keypoints import Keypoints2DInstances as Keypoints2DInstances
from tlc.core.helpers.keypoint_helper import KeypointHelper as KeypointHelper
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema
from typing import Any

class PoseEstimationMetricsCollectionCallback(MetricsCollectionCallback):
    """Callback for collecting predictions from SuperGradients pose estimation models."""
    @property
    def label_column_name(self) -> str: ...
    def compute_metrics(self, images: list[str], predictions: ImagesPoseEstimationPrediction | ImagePoseEstimationPrediction, table: Table) -> dict[str, Any]:
        """Compute metrics from a batch of data and corresponding predictions."""
    def metrics_column_schemas(self, table: Table) -> dict[str, Schema]:
        """Return the column schemas for the metrics of this callback."""
