from _typeshed import Incomplete
from enum import Enum
from pycocotools.coco import COCO
from tlc.client.sample_type import InstanceSegmentationMasks as InstanceSegmentationMasks, InstanceSegmentationPolygons as InstanceSegmentationPolygons
from tlc.core.builtins.constants.column_names import BOUNDING_BOXES as BOUNDING_BOXES, BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, HEIGHT as HEIGHT, IMAGE as IMAGE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, INSTANCE_PROPERTIES as INSTANCE_PROPERTIES, IS_CROWD as IS_CROWD, KEYPOINTS_2D as KEYPOINTS_2D, LABEL as LABEL, RLES as RLES, SEGMENTATION as SEGMENTATION, SEGMENTATIONS as SEGMENTATIONS, WIDTH as WIDTH, X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.builtins.constants.display_importances import DISPLAY_IMPORTANCE_BOUNDING_BOX as DISPLAY_IMPORTANCE_BOUNDING_BOX, DISPLAY_IMPORTANCE_IMAGE as DISPLAY_IMPORTANCE_IMAGE
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_MIN_X as NUMBER_ROLE_BB_MIN_X, NUMBER_ROLE_BB_MIN_Y as NUMBER_ROLE_BB_MIN_Y, NUMBER_ROLE_BB_SIZE_X as NUMBER_ROLE_BB_SIZE_X, NUMBER_ROLE_BB_SIZE_Y as NUMBER_ROLE_BB_SIZE_Y
from tlc.core.builtins.constants.string_roles import STRING_ROLE_FOLDER_URL as STRING_ROLE_FOLDER_URL, STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.builtins.schemas import BoundingBoxListSchema as BoundingBoxListSchema, SegmentationSchema as SegmentationSchema
from tlc.core.builtins.schemas.geometries import Keypoints2DSchema as Keypoints2DSchema
from tlc.core.data_formats.bounding_boxes import TopLeftXYWHBoundingBox as TopLeftXYWHBoundingBox
from tlc.core.data_formats.keypoints import Keypoints2DInstances as Keypoints2DInstances
from tlc.core.data_formats.segmentation import CocoRle as CocoRle
from tlc.core.helpers.segmentation_helper import SegmentationHelper as SegmentationHelper
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.in_memory_rows_table import SkipRow as SkipRow, _InMemoryRowsTable
from tlc.core.schema import BoolValue as BoolValue, ImageUrlStringValue as ImageUrlStringValue, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any, Literal

SEGMENTATION_FORMATS: Incomplete
logger: Incomplete

class CocoMode(Enum):
    DETECT = 'detect'
    SEGMENT = 'segment'
    KEYPOINTS = 'pose'
    STUFF_SEGMENTATION = 'stuff_segmentation'
    PANOPTIC_SEGMENTATION = 'panoptic_segmentation'
    IMAGE_CAPTIONING = 'image_captioning'
    DENSE_POSE = 'dense_pose'

class TableFromCoco(_InMemoryRowsTable):
    """A table populated from a COCO format annotations JSON file and associated image folder.

    This class provides functionality to load and process datasets in the COCO (Common Objects in Context) format,
    supporting both object detection and instance segmentation tasks. It can handle both crowd and non-crowd
    annotations, and can be configured to output either polygons or masks.

    References:
    COCO data format: https://cocodataset.org/#format-data
    COCO data format APIs: https://github.com/cocodataset/cocoapi
    """
    include_iscrowd: Incomplete
    input_url: Incomplete
    image_folder_url: Incomplete
    keep_crowd_annotations: Incomplete
    task: str
    segmentation_format: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, input_url: Url | str | None = None, image_folder_url: Url | str | None = None, include_iscrowd: bool | None = None, keep_crowd_annotations: bool | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None, task: Literal['detect', 'segment', 'pose'] | None = None, segmentation_format: Literal['polygons', 'masks'] | None = None, points: list[float] | None = None, point_attributes: list[str] | list[dict[str, str]] | None = None, lines: list[int] | None = None, line_attributes: list[str] | list[dict[str, str]] | None = None, triangles: list[int] | None = None, triangle_attributes: list[str] | list[dict[str, str]] | None = None, flip_indices: list[int] | None = None, oks_sigmas: list[float] | None = None, per_instance_schemas: dict[str, Schema] | None = None) -> None:
        '''Initialize a TableFromCoco object.

        :param url: The URL of the table.
        :param created: The creation date of the table.
        :param description: The description of the table.
        :param row_cache_url: The URL of the row cache.
        :param row_cache_populated: Whether the row cache is populated.
        :param override_table_rows_schema: The table rows schema to override.
        :param input_url: The URL of the input data.
        :param image_folder_url: The URL of the image folder.
        :param include_iscrowd: Whether to include the per-instance iscrowd flag in the table rows.
        :param keep_crowd_annotations: Whether to keep annotations with iscrowd=1.
        :param input_tables: A list of Table Urls that should be used as input tables.
        :param task: The task to perform (detect, segment or pose).
        :param segmentation_format: The format of the segmentation (polygons or masks).
        :param points: Default keypoint coordinates, used for drawing new instances in the Dashboard. Pose only.
        :param point_attributes: Attributes for each keypoint (e.g. name or color). Pose only.
        :param lines: Default skeleton topology for pose. Will override the skeleton provided in the annotations file.
            Pose only.
        :param line_attributes: Attributes for each line (e.g. name or color). Pose only.
        :param triangles: Triangles for pose.
        :param triangle_attributes: Attributes for each triangle (e.g. name or color). Pose only.
        :param flip_indices: Flip indices for pose.
        :param oks_sigmas: OKS sigmas for pose.
        :param per_instance_schemas: Schemas for any additional metadata to store per instance, e.g. "area" or "id".
            These values should be present in every annotation in the annotations file and match the schema provided.
            Currently only supported for task \'pose\'.
        '''
    @property
    def coco(self) -> COCO:
        """Load COCO object from input_url if not already loaded."""
