from _typeshed import Incomplete
from super_gradients.training.datasets.pose_estimation_datasets.abstract_pose_estimation_dataset import AbstractPoseEstimationDataset
from super_gradients.training.samples import PoseEstimationSample
from super_gradients.training.transforms.keypoint_transforms import AbstractKeypointTransform as AbstractKeypointTransform
from tlc.core.builtins.constants.column_names import IMAGE as IMAGE, KEYPOINTS_2D as KEYPOINTS_2D
from tlc.core.data_formats.keypoints import Keypoints2DInstances as Keypoints2DInstances
from tlc.core.helpers.keypoint_helper import KeypointHelper as KeypointHelper
from tlc.core.objects.table import Table as Table

class PoseEstimationDataset(AbstractPoseEstimationDataset):
    """Dataset class for training pose estimation models on Animal Pose dataset."""
    table: Incomplete
    keypoints_column: Incomplete
    image_column: Incomplete
    def __init__(self, table: Table, transforms: list[AbstractKeypointTransform], image_column: str = ..., keypoints_column: str = ...) -> None:
        """ """
    oks_sigmas: Incomplete
    flip_indices: Incomplete
    def check_table(self, table: Table, image_column: str = ..., keypoints_column: str = ...) -> tuple[int, list[tuple[int, int, int]] | None, list[tuple[int, int, int]] | None, list[tuple[int, int, int]] | None]:
        """Check compatibility of the table with the dataset, and return keypoint and edge information"""
    def __len__(self) -> int: ...
    def load_sample(self, index: int) -> PoseEstimationSample:
        """Load a sample from the dataset"""

def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert #RRGGBB to (R, G, B)"""
def rgb_to_hex(rgb_color: tuple[int, int, int]) -> str:
    """Convert (R, G, B) to #RRGGBB"""
