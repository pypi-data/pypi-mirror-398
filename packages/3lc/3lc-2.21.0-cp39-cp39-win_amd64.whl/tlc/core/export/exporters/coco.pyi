from _typeshed import Incomplete
from collections.abc import Generator, Iterator, Mapping
from dataclasses import dataclass
from tlc.core.builtins.constants.column_names import BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, HEIGHT as HEIGHT, IMAGE as IMAGE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, INSTANCES as INSTANCES, INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, INSTANCE_PROPERTIES as INSTANCE_PROPERTIES, IS_CROWD as IS_CROWD, LABEL as LABEL, RLES as RLES, WIDTH as WIDTH, X_MAX as X_MAX, Y_MAX as Y_MAX
from tlc.core.data_formats.bounding_boxes import BoundingBox as BoundingBox, SegmentationBoundingBox as SegmentationBoundingBox, TopLeftXYWHBoundingBox as TopLeftXYWHBoundingBox, XYXYBoundingBox as XYXYBoundingBox
from tlc.core.export.exporter import Exporter as Exporter, register_exporter as register_exporter
from tlc.core.helpers.keypoint_helper import KeypointHelper as KeypointHelper
from tlc.core.objects.table import Table as Table
from tlc.core.schema import MapElement as MapElement, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from typing import Any, Callable

logger: Incomplete

def parse_include_segmentation_arg(include_segmentation: bool | str | None) -> bool | None: ...

class COCOExporter(Exporter):
    """Exporter for the COCO format.

    Tables which are originally instances of the TableFromCoco class will be compatible with this exporter.
    """
    supported_format: str
    priority: int
    @classmethod
    def can_export(cls, table: Table, output_url: Url) -> bool:
        """Check if the table can be exported to the COCO format.

        Can not be 100% accurate, as we don't know if the user has supplied additional arguments, such as
        annotation_column_name, or image_column_name.
        """
    @classmethod
    def serialize(cls, table: Table, output_url: Url, weight_threshold: float = 0.0, image_folder: Url | str = '', absolute_image_paths: bool = False, include_segmentation: bool | None = None, annotation_column_name: str | None = None, image_column_name: str | None = None, indent: int = 4, **kwargs: Any) -> str:
        """Serialize a table to the COCO format.

        Default behavior is to write a COCO file with image paths relative to the (output) annotations file. Written
        paths can be further configured with the `absolute_image_paths` and `image_folder` argument.

        Note that for a coco file to be valid, the image paths should be absolute or relative w.r.t. the annotations
        file itself.

        :param table: The table to serialize
        :param output_url: The output URL
        :param weight_threshold: The weight threshold
        :param image_folder: Make image paths relative to a specific folder. Note that this may produce an annotations
            file that needs special handling. This option is mutually exclusive with `absolute_image_paths`.
        :param absolute_image_paths: Make image paths absolute. If this is set to True, the `image_folder` cannot be
            set.
        :param include_segmentation: Whether to include segmentation in the exported COCO file. If this flag is True,
            segmentation poly-lines will be generated directly from the bounding box annotations. If this flag is False,
            no segmentations are written. If this flag is None, segmentation info will be copied directly from the input
            Table.
        :param annotation_column_name: Optional column name to use for annotations instead of the defaults
            (`bbs`, `segmentations`, or `keypoints_2d`). The content of the column determines the
            annotation mode (bounding boxes, segmentations, or keypoints) based on its structure.
        :param image_column_name: Optional column name to use for image URLs. Defaults to `image`.
        :param indent: The number of spaces to use for indentation in the output.
        :param kwargs: Any additional arguments
        :return: The serialized table
        """

@dataclass
class _COCOInstance:
    segmentation: list[list[float]]
    bounding_box: BoundingBox
    is_crowd: bool
    label: float
    keypoints: list[float]
    id: int
    extras: dict[str, Any]

class _InstanceIterator:
    """Yields all instances in a table row."""
    table_row: Incomplete
    idx: Incomplete
    is_old_style_bb: Incomplete
    is_seg: Incomplete
    is_keypoints: Incomplete
    include_segmentation: Incomplete
    bb_type: Incomplete
    annotation_idx: Incomplete
    annotation_column: Incomplete
    def __init__(self, table_row: Mapping[str, object], idx: int, annotation_idx: int, is_old_style_bb: bool, is_seg: bool, is_keypoints: bool, include_segmentation: bool | None, bb_type: Callable[..., BoundingBox] | None, annotation_column: str) -> None: ...
    def __iter__(self) -> Iterator[_COCOInstance]: ...
    def generate_instances(self) -> Generator[_COCOInstance, None, None]: ...
