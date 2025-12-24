import abc
from _typeshed import Incomplete
from pyarrow.lib import Array as Array
from tlc.client.sample_type import CategoricalLabel as CategoricalLabel, InstanceSegmentationPolygons as InstanceSegmentationPolygons
from tlc.core.builtins.constants.column_names import BOUNDING_BOXES as BOUNDING_BOXES, BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, HEIGHT as HEIGHT, IMAGE as IMAGE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, KEYPOINTS_2D as KEYPOINTS_2D, LABEL as LABEL, ORIENTED_BBS_2D as ORIENTED_BBS_2D, SEGMENTATIONS as SEGMENTATIONS, WIDTH as WIDTH, X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_CENTER_X as NUMBER_ROLE_BB_CENTER_X, NUMBER_ROLE_BB_CENTER_Y as NUMBER_ROLE_BB_CENTER_Y, NUMBER_ROLE_BB_SIZE_X as NUMBER_ROLE_BB_SIZE_X, NUMBER_ROLE_BB_SIZE_Y as NUMBER_ROLE_BB_SIZE_Y
from tlc.core.builtins.constants.string_roles import STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.builtins.constants.units import UNIT_RELATIVE as UNIT_RELATIVE
from tlc.core.builtins.schemas import BoundingBoxListSchema as BoundingBoxListSchema
from tlc.core.builtins.schemas.geometries import Keypoints2DSchema as Keypoints2DSchema, OrientedBoundingBoxes2DSchema as OrientedBoundingBoxes2DSchema
from tlc.core.data_formats.keypoints import Keypoints2DInstances as Keypoints2DInstances
from tlc.core.data_formats.obb import OBB2DInstances as OBB2DInstances
from tlc.core.data_formats.segmentation import SegmentationPolygonsDict as SegmentationPolygonsDict
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, ImageUrlStringValue as ImageUrlStringValue, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

logger: Incomplete

class _SkipInstance(Exception): ...

class _TableFromYolo(_InMemoryColumnsTable, abc.ABC, metaclass=abc.ABCMeta):
    '''A table populated from a YOLO dataset, defined by a YAML file and a split.

    The `TableFromYolo` class is an interface between 3LC and the YOLO data format. The YAML file must contain the
    keys `path`, `names` and the provided `split`. If the path in the YAML file is relative, a set of alternatives are
    tried: The directory with the YAML file, the parent of this directory and the
    current working directory.

    :Example:
    ```python
    table = TableFromYolo(
        input_url="path/to/yaml/file.yaml",
        split="train",
    )
    print(table.table_rows[0])
    ```

    :param input_url: The Url to the YOLO YAML file to parse.
    :param split: The split of the dataset to use. Default is "val".
    :param datasets_dir_url: The Url to prepend to the \'path\' in the YAML file if it is relative. If not provided, the
        directory where the YAML sits is used.
    :param override_split_path: A list of paths to override the paths in the YAML file. If provided, the \'path\' and
        \'<split>\' in the YAML file are ignored.
    '''
    input_url: Url
    split: Incomplete
    datasets_dir: Url | None
    override_split_path: list[str] | None
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, input_url: Url | str | None = None, split: str | None = None, datasets_dir: Url | None = None, override_split_path: list[str] | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None, **kwargs: Any) -> None: ...

class _YoloDetectionTaskHandler: ...
class _YoloSegmentationTaskHandler: ...
class TableFromYoloDetection(_YoloDetectionTaskHandler, _TableFromYolo): ...
class TableFromYoloSegmentation(_YoloSegmentationTaskHandler, _TableFromYolo): ...
class TableFromYolo(TableFromYoloDetection): ...

class TableFromYoloKeypoints(_TableFromYolo):
    """A table populated from a YOLO keypoints dataset.

    The keypoints are stored in YOLO label format, which consists of a single file per image, where each line contains
    the class index, the bounding box coordinates and the keypoint coordinates.

    The dataset YAML file must contain the keys `path`, `names` and the provided `split`. For pose estimation tasks,
    only a single class is expected.

    In addition, the dataset YAML file should contain the ultralytics-compatible keys `kpt_shape`, which is a list of
    two integers, the first being the number of keypoints and the second being the number of channels; 2 for keypoints
    only, 3 for keypoints with visibility flag, and `flip_idx`, which are stored in the Table's
    Schema, enabling flip-augmentation when used during training.

    Finally, for convenience, all keypoint related arguments can also be provided in the dataset yaml file.

    See (Table.from_yolo) for descriptions of all arguments.
    """
    points: Incomplete
    point_attributes: Incomplete
    lines: Incomplete
    line_attributes: Incomplete
    triangles: Incomplete
    triangle_attributes: Incomplete
    flip_indices: Incomplete
    oks_sigmas: Incomplete
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

class TableFromYoloOBB(_TableFromYolo):
    """A table populated from a YOLO OBB dataset."""
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    @staticmethod
    def regularize_obb(center: tuple[float, float], size: tuple[float, float], angle_deg: float) -> tuple[tuple[float, float], tuple[float, float], float]:
        """Ensure angle is in the first quadrant [0, pi/2), flip w, h if necessary

        :param center: The center of the OBB.
        :param size: The size of the OBB.
        :param angle_deg: The angle of the OBB in degrees.
        :return: The regularized OBB.
        """
