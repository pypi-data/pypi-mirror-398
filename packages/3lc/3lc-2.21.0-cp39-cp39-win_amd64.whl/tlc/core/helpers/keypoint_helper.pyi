import numpy as np
from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.core.builtins.constants.column_names import FLIP_INDICES as FLIP_INDICES, INSTANCES as INSTANCES, KEYPOINTS_2D as KEYPOINTS_2D, LINES as LINES, LINES_ADDITIONAL_DATA as LINES_ADDITIONAL_DATA, LINE_ROLE as LINE_ROLE, OKS_SIGMAS as OKS_SIGMAS, TRIANGLES as TRIANGLES, TRIANGLES_ADDITIONAL_DATA as TRIANGLES_ADDITIONAL_DATA, TRIANGLE_ROLE as TRIANGLE_ROLE, VERTEX_ROLE as VERTEX_ROLE, VERTICES_2D as VERTICES_2D, VERTICES_2D_ADDITIONAL_DATA as VERTICES_2D_ADDITIONAL_DATA
from tlc.core.builtins.schemas.schemas import Int32ListSchema as Int32ListSchema
from tlc.core.objects.table import Table as Table
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, NumericValue as NumericValue, Schema as Schema
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlcurl.url import Url as Url
from typing import Any, ClassVar

logger: Incomplete

class KeypointHelper:
    """Static helpers to read keypoint geometry and metadata from 3LC Tables.

    Includes COCO defaults (names, skeleton, colors, flip indices) for convenience.
    """
    COCO_KEYPOINT_NAMES: ClassVar[list[str]]
    COCO_KEYPOINT_DEFAULT_POSE: ClassVar[list[float]]
    COCO_SKELETON: ClassVar[list[int]]
    COCO_SKELETON_COLORS: ClassVar[list[tuple[int, int, int]]]
    COCO_SKELETON_NAMES: ClassVar[list[str]]
    COCO_FLIP_INDICES: ClassVar[list[int]]
    @staticmethod
    def get_keypoint_shape_from_table(table: Table, label_column_name: str = ...) -> list[int] | None:
        """Return [num_keypoints, num_channels] inferred from the table, or None.

        Channels: 2 => x,y only; 3 => x,y plus an extra channel (e.g., visibility).
        """
    @staticmethod
    def get_points_from_table(table: Table, label_column_name: str = ...) -> list[float] | None:
        """Return default vertex coordinates ([x0, y0, ...]) or None."""
    @staticmethod
    def get_keypoint_attributes_from_table(table: Table, label_column_name: str = ...) -> list[dict[str, Any]] | None:
        """Return keypoint attribute dicts (e.g., names/ids) from the schema, or None."""
    @staticmethod
    def get_lines_from_table(table: Table, label_column_name: str = ...) -> list[int] | None:
        """Return flattened skeleton index pairs [i0, j0, i1, j1, ...], or None."""
    @staticmethod
    def get_line_attributes_from_table(table: Table, label_column_name: str = ...) -> list[dict[str, Any]] | None:
        """Return line attribute dicts (matching the skeleton order), or None."""
    @staticmethod
    def get_triangles_from_table(table: Table, label_column_name: str = ...) -> list[int] | None:
        """Return flattened triangle index triplets [i, j, k, ...], or None."""
    @staticmethod
    def get_triangle_attributes_from_table(table: Table, label_column_name: str = ...) -> list[dict[str, Any]] | None:
        """Return triangle attribute dicts (matching the triangle order), or None."""
    @staticmethod
    def get_oks_sigmas_from_table(table: Table, label_column_name: str = ...) -> list[float] | None:
        """Return OKS sigma values list, or None."""
    @staticmethod
    def get_flip_indices_from_table(table: Table, label_column_name: str = ...) -> list[int] | None:
        """Return horizontal flip index mapping list, or None."""
    @staticmethod
    def flatten_points(points: Sequence[float] | Sequence[Sequence[float]] | np.ndarray) -> list[float]:
        """Returns a flat list of points.

        :param points: Can be lists of (x,y) or (x, y, z), numpy arrays or nested lists.
        :return: A flat list of points
        """
    @staticmethod
    def flatten_lines(lines: Sequence[int] | Sequence[Sequence[int]] | np.ndarray) -> list[int]:
        """Returns a flat list of lines.

        :param lines: Can be lists of (i0, j0, i1, j1, ...), numpy arrays or nested lists.
        :return: A flat list of lines
        """
    @staticmethod
    def flatten_triangles(triangles: Sequence[int] | Sequence[Sequence[int]] | np.ndarray) -> list[int]:
        """Returns a flat list of triangles.

        :param triangles: Can be lists of (i, j, k, ...), numpy arrays or nested lists.
        :return: A flat list of triangles
        """
    @staticmethod
    def parse_keypoints_with_visibility(keypoints: list[float] | list[list[float]] | list[tuple[float, float]] | np.ndarray) -> tuple[np.ndarray, np.ndarray | None]:
        """Parse keypoints in various formats, extracting coordinates and optional visibility.

        :param keypoints: Keypoints in one of these formats:
            - Flat list: [x1, y1, x2, y2, ...] or [x1, y1, v1, x2, y2, v2, ...]
            - List of pairs: [[x1, y1], [x2, y2], ...]
            - List of triplets: [[x1, y1, v1], [x2, y2, v2], ...]
            - NumPy array of shape (K, 2) or (K, 3)
        :returns: Tuple of (keypoints_array, visibility_array)
            - keypoints_array: shape (K, 2) with x,y coordinates
            - visibility_array: shape (K,) with visibility flags, or None if not present
        """
    @staticmethod
    def parse_bbox(bbox: list[float] | tuple[float, float, float, float] | np.ndarray, format: str = 'xyxy') -> np.ndarray:
        '''Parse bounding box in various formats.

        :param bbox: Bounding box as list, tuple, or array
        :param format: Currently only "xyxy" is supported
        :returns: Array of shape (1, 4) with [x_min, y_min, x_max, y_max]
        '''
    @staticmethod
    def parse_per_keypoint_channel(num_keypoints: int, visibility: list[int] | np.ndarray | None = None, confidence: list[float] | np.ndarray | None = None, derived_visibility: np.ndarray | None = None) -> tuple[np.ndarray | None, np.ndarray | None]:
        """Parse and validate per-keypoint visibility or confidence channel.

        :param num_keypoints: Expected number of keypoints
        :param visibility: Optional visibility values
        :param confidence: Optional confidence values
        :param derived_visibility: Optional visibility derived from keypoint parsing
        :returns: Tuple of (visibility_array, confidence_array), both shape (1, K) or None
        :raises ValueError: If both visibility and confidence are provided
        """
    @staticmethod
    def edit_oks_sigmas(table: Table, oks_sigmas: list[float] | None = None, label_column_name: str = ..., table_name: str = 'edited_oks_sigmas', *, table_url: Url | None = None) -> Table:
        """Edit the OKS sigmas for a keypoint column in a Table.

        :param table: The Table to edit
        :param oks_sigmas: The new OKS sigmas
        :param label_column_name: The name of the keypoint column to edit
        :param table_name: The name of the new table
        :param table_url: The URL of the new table
        :returns: The edited Table
        """
    @staticmethod
    def edit_default_keypoints(table: Table, keypoints: list[float] | list[list[float]] | list[tuple[float, float]] | np.ndarray, label_column_name: str = ..., table_name: str = 'edited_default_keypoints', *, table_url: Url | None = None) -> Table:
        """Edit the default keypoints for a keypoint column in a Table.

        The default keypoint values will be stored in the Table's rows schema and used for drawing new instances in the
        3LC Dashboard.

        :param table: The Table to edit
        :param keypoints: The new keypoints
        :param label_column_name: The name of the keypoint column to edit
        :param table_name: The name of the new table
        :param table_url: The URL of the new table
        :returns: The edited Table
        """
    @staticmethod
    def edit_default_lines(table: Table, lines: list[int] | list[list[int]] | np.ndarray, label_column_name: str = ..., table_name: str = 'edited_default_lines', *, table_url: Url | None = None) -> Table:
        """Edit the default lines for a keypoint column in a Table."""
