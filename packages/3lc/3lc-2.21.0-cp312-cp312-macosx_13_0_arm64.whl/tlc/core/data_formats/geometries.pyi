import numpy as np
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from tlc.core.builtins.constants.column_names import BBS_2D as BBS_2D, BBS_3D as BBS_3D, CENTER_X as CENTER_X, CENTER_Y as CENTER_Y, CENTER_Z as CENTER_Z, INSTANCES as INSTANCES, INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, LINES as LINES, LINES_ADDITIONAL_DATA as LINES_ADDITIONAL_DATA, ORIENTED_BBS_2D as ORIENTED_BBS_2D, ORIENTED_BBS_3D as ORIENTED_BBS_3D, PITCH as PITCH, ROLL as ROLL, ROTATION as ROTATION, SIZE_X as SIZE_X, SIZE_Y as SIZE_Y, SIZE_Z as SIZE_Z, TRIANGLES as TRIANGLES, TRIANGLES_ADDITIONAL_DATA as TRIANGLES_ADDITIONAL_DATA, VERTICES_2D as VERTICES_2D, VERTICES_2D_ADDITIONAL_DATA as VERTICES_2D_ADDITIONAL_DATA, VERTICES_3D as VERTICES_3D, VERTICES_3D_ADDITIONAL_DATA as VERTICES_3D_ADDITIONAL_DATA, X_MAX as X_MAX, X_MIN as X_MIN, YAW as YAW, Y_MAX as Y_MAX, Y_MIN as Y_MIN, Z_MAX as Z_MAX, Z_MIN as Z_MIN
from typing import Any

@dataclass
class Geometry2DInstances:
    """Container for 2D geometry instances.

    Supports all primitives: vertices, lines, triangles, axis-aligned bounding boxes, and oriented bounding boxes.

    ::: {note}
    Extras (per_point, per_line, per_triangle, per_instance) support scalars, fixed-size arrays, and composite Python
    objects (e.g., dicts).
    :::
    """
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    vertices: list[np.ndarray]
    per_vertex_extras: dict[str, list[np.ndarray]]
    lines: list[np.ndarray]
    per_line_extras: dict[str, list[np.ndarray]]
    triangles: list[np.ndarray]
    per_triangle_extras: dict[str, list[np.ndarray]]
    bbs_2d: list[np.ndarray]
    oriented_bbs_2d: list[np.ndarray]
    per_instance_extras: dict[str, np.ndarray]
    @classmethod
    def create_empty(cls, x_min: float = 0.0, y_min: float = 0.0, x_max: float = 0.0, y_max: float = 0.0, per_vertex_extras_keys: Sequence[str] | None = None, per_line_extras_keys: Sequence[str] | None = None, per_triangle_extras_keys: Sequence[str] | None = None, instance_extras_keys: Sequence[str] | None = None) -> Geometry2DInstances:
        """Create an empty Geometry2DInstances container.

        :param x_min: Minimum x coordinate (default 0.0)
        :param y_min: Minimum y coordinate (default 0.0)
        :param x_max: Maximum x coordinate
        :param y_max: Maximum y coordinate
        :param per_vertex_extras_keys: Sequence of keys for per-vertex additional data to initialize
        :param per_line_extras_keys: Sequence of keys for per-line additional data to initialize
        :param per_triangle_extras_keys: Sequence of keys for per-triangle additional data to initialize
        :param instance_extras_keys: Sequence of keys for per-instance additional data to initialize
        :raises ValueError: If bounds are invalid (e.g., x_max < x_min)
        """
    def add_instance(self, vertices: np.ndarray, lines: np.ndarray | None = None, triangles: np.ndarray | None = None, bbs_2d: np.ndarray | None = None, oriented_bbs_2d: np.ndarray | None = None, per_vertex_extras: Mapping[str, np.ndarray] | None = None, per_line_extras: Mapping[str, np.ndarray] | None = None, per_triangle_extras: Mapping[str, np.ndarray] | None = None, per_instance_extras: Mapping[str, Any] | None = None) -> None:
        """Add a 2D instance.

        :param vertices: Array of shape (N, 2) or flattened (2N,), dtype float32
        :param per_vertex_extras: Dict of arrays of shape (N,)
        :param per_instance_extras: Dict of scalar per-instance attributes (one value or length-1 array)
        :param lines: Flattened int array (2L,) of vertex indices forming L line segments
        :param triangles: Flattened int array (3T,) of vertex indices forming T triangles
        :param bbs_2d: Array of shape (B, 4) or flattened (4B,), dtype float32
        :param oriented_bbs_2d: Array of shape (O, 5) or flattened (5O,), dtype float32
        :param per_line_extras: Dict of arrays of shape (L,) for per-line extras
        :param per_triangle_extras: Dict of arrays of shape (T,) for per-triangle extras
        :raises ValueError: On shape/type/index validation errors
        """
    def to_row(self) -> dict[str, Any]:
        """Convert to the internal 3LC row format used by Geometry2D columns."""
    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Geometry2DInstances:
        """Parse a Geometry2D row into a Geometry2DInstances object.

        :param row: Row dictionary with INSTANCES, X_MIN, Y_MIN, X_MAX, Y_MAX keys
        :raises ValueError: If bounds are missing or invalid
        """

@dataclass
class Geometry3DInstances:
    """Container for 3D geometry instances.

    Supports all primitives: vertices, lines, triangles, axis-aligned bounding boxes, and oriented bounding boxes.

    ::: {note}
    Extras (per_point, per_line, per_triangle, per_instance) support scalars, fixed-size arrays, and composite Python
    objects (e.g., dicts).
    :::
    """
    x_min: float
    y_min: float
    z_min: float
    x_max: float
    y_max: float
    z_max: float
    vertices: list[np.ndarray]
    per_vertex_extras: dict[str, list[np.ndarray]]
    lines: list[np.ndarray]
    per_line_extras: dict[str, list[np.ndarray]]
    triangles: list[np.ndarray]
    per_triangle_extras: dict[str, list[np.ndarray]]
    bbs_3d: list[np.ndarray]
    oriented_bbs_3d: list[np.ndarray]
    per_instance_extras: dict[str, np.ndarray]
    @classmethod
    def create_empty(cls, x_min: float = 0.0, x_max: float = 0.0, y_min: float = 0.0, y_max: float = 0.0, z_min: float = 0.0, z_max: float = 0.0, per_vertex_extras_keys: Sequence[str] | None = None, per_line_extras_keys: Sequence[str] | None = None, per_triangle_extras_keys: Sequence[str] | None = None, instance_extras_keys: Sequence[str] | None = None) -> Geometry3DInstances:
        """Create an empty Geometry3DInstances container.

        :param x_min: Minimum x coordinate (default 0.0)
        :param x_max: Maximum x coordinate
        :param y_min: Minimum y coordinate (default 0.0)
        :param y_max: Maximum y coordinate
        :param z_min: Minimum z coordinate (default 0.0)
        :param z_max: Maximum z coordinate
        :param per_vertex_extras_keys: Sequence of keys for per-vertex additional data to initialize
        :param per_line_extras_keys: Sequence of keys for per-line additional data to initialize
        :param per_triangle_extras_keys: Sequence of keys for per-triangle additional data to initialize
        :param instance_extras_keys: Sequence of keys for per-instance additional data to initialize
        :raises ValueError: If bounds are not fully specified
        """
    def add_instance(self, vertices: np.ndarray, lines: np.ndarray | None = None, triangles: np.ndarray | None = None, bbs_3d: np.ndarray | None = None, oriented_bbs_3d: np.ndarray | None = None, per_vertex_extras: Mapping[str, np.ndarray] | None = None, per_line_extras: Mapping[str, np.ndarray] | None = None, per_triangle_extras: Mapping[str, np.ndarray] | None = None, per_instance_extras: Mapping[str, Any] | None = None) -> None:
        """Add a 3D instance.

        :param vertices: Array of shape (N, 3) or flattened (3N,), dtype float32
        :param lines: Flattened int array (2L,) of vertex indices forming L line segments
        :param triangles: Flattened int array (3T,) of vertex indices forming T triangles
        :param bbs_3d: Array of shape (B, 6) or flattened (6B,), dtype float32
        :param oriented_bbs_3d: Array of shape (O, 9) or flattened (9O,), dtype float32
        :param per_vertex_extras: Dict of arrays of shape (N,)
        :param per_line_extras: Dict of arrays of shape (L,) for per-line extras
        :param per_triangle_extras: Dict of arrays of shape (T,) for per-triangle extras
        :param per_instance_extras: Dict of scalar per-instance attributes (one value or length-1 array)
        :raises ValueError: On shape/type/index validation errors
        """
    def to_row(self) -> dict[str, Any]:
        """Convert to the internal 3LC row format used by Geometry3D columns."""
    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> Geometry3DInstances:
        """Parse a Geometry3D row into a Geometry3DInstances object.

        :param row: Row dictionary with INSTANCES, X_MIN, Y_MIN, Z_MIN, X_MAX, Y_MAX, Z_MAX keys
        :raises ValueError: If bounds are missing or invalid
        """
