import numpy as np
from tlc.core.builtins.constants.column_names import BBS_2D as BBS_2D, BBS_3D as BBS_3D, CENTER_X as CENTER_X, CENTER_Y as CENTER_Y, CENTER_Z as CENTER_Z, CONFIDENCE as CONFIDENCE, FLIP_INDICES as FLIP_INDICES, INSTANCES as INSTANCES, INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, LABEL as LABEL, LINES as LINES, LINES_ADDITIONAL_DATA as LINES_ADDITIONAL_DATA, LINE_ROLE as LINE_ROLE, OKS_SIGMAS as OKS_SIGMAS, ORIENTED_BBS_2D as ORIENTED_BBS_2D, ORIENTED_BBS_3D as ORIENTED_BBS_3D, PITCH as PITCH, ROLL as ROLL, ROTATION as ROTATION, SIZE_X as SIZE_X, SIZE_Y as SIZE_Y, SIZE_Z as SIZE_Z, TRIANGLES as TRIANGLES, TRIANGLES_ADDITIONAL_DATA as TRIANGLES_ADDITIONAL_DATA, TRIANGLE_ROLE as TRIANGLE_ROLE, VERTEX_ROLE as VERTEX_ROLE, VERTICES_2D as VERTICES_2D, VERTICES_2D_ADDITIONAL_DATA as VERTICES_2D_ADDITIONAL_DATA, VERTICES_3D as VERTICES_3D, VERTICES_3D_ADDITIONAL_DATA as VERTICES_3D_ADDITIONAL_DATA, VISIBILITY as VISIBILITY, X_MAX as X_MAX, X_MIN as X_MIN, YAW as YAW, Y_MAX as Y_MAX, Y_MIN as Y_MIN, Z_MAX as Z_MAX, Z_MIN as Z_MIN
from tlc.core.builtins.schemas.schemas import CategoricalLabelListSchema as CategoricalLabelListSchema, Float32ListSchema as Float32ListSchema, Int32ListSchema as Int32ListSchema
from tlc.core.helpers.keypoint_helper import KeypointHelper as KeypointHelper
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, MapElement as MapElement, Schema as Schema, ValueMapLike as ValueMapLike
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from typing import Any

class BoundingBox3DSchema(Schema):
    """Defines a single axis-aligned 3D bounding box defined by minimum and maximum values on each axis."""
    def __init__(self, is_list: bool = False, **schema_kwargs: Any) -> None: ...

class OrientedBoundingBox3DSchema(Schema):
    """Defines a single 3D oriented bounding box defined by center position, size along each axis,
    and orientation (yaw, pitch, roll in radians)."""
    def __init__(self, is_list: bool = False, **schema_kwargs: Any) -> None: ...

class BoundingBox2DSchema(Schema):
    """Defines a single axis-aligned 2D bounding box defined by minimum and maximum values on X and Y."""
    def __init__(self, is_list: bool = False, **schema_kwargs: Any) -> None: ...

class OrientedBoundingBox2DSchema(Schema):
    """Defines a single 2D oriented bounding box defined by center position, size, and rotation (radians)."""
    def __init__(self, is_list: bool = False, **schema_kwargs: Any) -> None: ...

class GeometrySchema(Schema):
    """Base class for 2D/3D geometry collections.

    Each instance can optionally include points, lines, and triangles with additional per-element attributes.
    Per-instance attributes can also be attached, for example labels and confidences.
    """
    def __init__(self, include_triangles: bool = False, include_lines: bool = False, per_line_schemas: dict[str, Schema] | None = None, per_triangle_schemas: dict[str, Schema] | None = None, per_instance_schemas: dict[str, Schema] | None = None, is_bulk_data: bool = False, **kwargs: Any) -> None:
        """
        :param include_lines: Whether instances include lines.
        :param include_triangles: Whether instances include triangles.
        :param per_line_schemas: Additional attributes attached to each line.
        :param per_triangle_schemas: Additional attributes attached to each triangle.
        :param per_instance_schemas: Additional attributes attached per instance.
        :param is_bulk_data: Declares that the data described by the Schema is bulk data. This will force any data added
            using a TableWriter to be stored as bulk data.
        :param kwargs: Additional keyword arguments forwarded to the base Schema.
        """

class Geometry3DSchema(GeometrySchema):
    """Schema root for 3D scenes with optional points, lines, triangles, and boxes.

    The root includes the overall axis-aligned extent of the scene.
    """
    def __init__(self, include_3d_vertices: bool = False, include_lines: bool = False, include_triangles: bool = False, include_3d_bounding_boxes: bool = False, include_3d_oriented_bounding_boxes: bool = False, per_vertex_schemas: dict[str, Schema] | None = None, per_triangle_schemas: dict[str, Schema] | None = None, per_line_schemas: dict[str, Schema] | None = None, per_instance_schemas: dict[str, Schema] | None = None, is_bulk_data: bool = False, **schema_kwargs: Any) -> None:
        """
        :param include_3d_vertices: Whether instances include 3D vertices.
        :param include_lines: Whether instances include lines.
        :param include_triangles: Whether instances include triangles.
        :param include_3d_bounding_boxes: Whether instances include axis-aligned 3D boxes.
        :param include_3d_oriented_bounding_boxes: Whether instances include oriented 3D boxes.
        :param per_vertex_schemas: Additional attributes attached to each 3D vertex.
        :param per_triangle_schemas: Additional attributes attached to each triangle.
        :param per_line_schemas: Additional attributes attached to each line.
        :param per_instance_schemas: Additional attributes attached per instance.
        :param is_bulk_data: Declares that the data described by the Schema is bulk data. This will force any data added
            using a TableWriter to be stored as bulk data.
        :param schema_kwargs: Additional keyword arguments forwarded to the base Schema.
        """

class Geometry2DSchema(GeometrySchema):
    """Schema root for 2D scenes with optional vertices, lines, triangles, and boxes.

    The root includes the overall axis-aligned extent of the scene.
    """
    def __init__(self, include_2d_vertices: bool = False, include_lines: bool = False, include_triangles: bool = False, include_2d_bounding_boxes: bool = False, include_2d_oriented_bounding_boxes: bool = False, per_vertex_schemas: dict[str, Schema] | None = None, per_line_schemas: dict[str, Schema] | None = None, per_triangle_schemas: dict[str, Schema] | None = None, per_instance_schemas: dict[str, Schema] | None = None, is_bulk_data: bool = False, **schema_kwargs: Any) -> None:
        """
        :param include_2d_vertices: Whether instances include 2D vertices.
        :param include_lines: Whether instances include lines.
        :param include_triangles: Whether instances include triangles.
        :param include_2d_bounding_boxes: Whether instances include axis-aligned 2D boxes.
        :param include_2d_oriented_bounding_boxes: Whether instances include oriented 2D boxes.
        :param per_vertex_schemas: Additional attributes attached to each 2D vertex.
        :param per_line_schemas: Additional attributes attached to each line.
        :param per_triangle_schemas: Additional attributes attached to each triangle.
        :param per_instance_schemas: Additional attributes attached per instance.
        :param is_bulk_data: Declares that the data described by the Schema is bulk data. This will force any data added
            using a TableWriter to be stored as bulk data.
        :param schema_kwargs: Additional keyword arguments forwarded to the base Schema.
        """

class Keypoints2DSchema(Geometry2DSchema):
    """Defines a schema for 2D keypoint instances.

    Adds a default set of points per instance and can include a default
    connectivity (lines) and mesh faces (triangles). Axis-aligned 2D boxes
    and per-instance labels are included by default.
    """
    def __init__(self, classes: str | ValueMapLike | None, num_keypoints: int, points: list[float] | list[list[float]] | np.ndarray | None = None, point_attributes: list[str] | list[dict[str, Any]] | None = None, lines: list[int] | list[list[int]] | np.ndarray | None = None, line_attributes: list[str] | list[dict[str, Any]] | None = None, triangles: list[int] | list[list[int]] | np.ndarray | None = None, triangle_attributes: list[str] | list[dict[str, Any]] | None = None, flip_indices: list[int] | None = None, oks_sigmas: list[float] | None = None, include_per_point_confidence: bool = False, include_per_point_visibility: bool = False, include_per_instance_label: bool = True, include_per_instance_confidence: bool = False, per_instance_schemas: dict[str, Schema] | None = None, **schema_kwargs: Any) -> None:
        '''
        :param classes: Class map or a single class name for per-instance labels, or None to skip labels.
        :param num_keypoints: Number of keypoints (> 0).
        :param points: Default relative keypoint coordinates used when creating new instances.
            Inputs may be nested; values are flattened internally. The flattened length must be
            num_keypoints*2 in the order [x0, y0, ..., xN-1, yN-1].
        :param point_attributes: Per-point role names in the same order as keypoints; defaults to
            ["kpt_0", ..., "kpt_{N-1}"].
        :param lines: Default connectivity as index pairs. Inputs may be nested; values are flattened
            internally to [i0, j0, i1, j1, ...].
        :param line_attributes: Per-line role names matching the number of line pairs.
        :param triangles: Default triangle faces as index triples. Inputs may be nested; values are
            flattened internally to [i0, j0, k0, i1, j1, k1, ...].
        :param triangle_attributes: Per-triangle role names matching the number of triangle triples.
        :param flip_indices: Indices used for horizontal-flip augmentation; stored with the points metadata.
        :param oks_sigmas: Object Keypoint Similarity (OKS) sigmas; defaults to uniform [1/num_keypoints]
            repeated num_keypoints times; stored with the points metadata.
        :param include_per_point_confidence: Whether to add a per-point confidence score (read-only).
        :param include_per_point_visibility: Whether to add a per-point visibility score with categories
            0.0=undefined, 1.0=occluded, 2.0=visible.
        :param include_per_instance_label: Whether to add a per-instance label.
        :param include_per_instance_confidence: Whether to add a per-instance confidence score.
        :param per_instance_schemas: Additional per-instance attributes.
        :param schema_kwargs: Additional keyword arguments forwarded to the base Schema.
        :raises ValueError: If num_keypoints <= 0.
        '''

class OrientedBoundingBoxes2DSchema(Geometry2DSchema):
    """Defines a user-facing schema for 2D oriented bounding boxes.

    By default this schema includes oriented 2D boxes and a label per object.
    It exposes the same include/override options as the 2D geometry schema so
    callers can flexibly add points, lines, triangles, or axis-aligned boxes.
    """
    def __init__(self, classes: str | ValueMapLike | None, include_per_instance_label: bool = True, include_per_instance_confidence: bool = False, per_instance_schemas: dict[str, Schema] | None = None, **schema_kwargs: Any) -> None:
        """
        :param classes: Class map or a single class name for instance labels, or None to skip labels.
        :param include_per_instance_label: Whether to add a per-instance label.
        :param include_per_instance_confidence: Whether to add a per-instance confidence score.
        :param per_instance_schemas: Additional per-instance schemas.
        :param schema_kwargs: Additional keyword arguments forwarded to base `Schema`.
        """

class OrientedBoundingBoxes3DSchema(Geometry3DSchema):
    """Defines a user-facing schema for 3D oriented bounding boxes.

    By default this schema includes oriented 3D boxes and a label per object.
    It exposes the same include/override options as the 3D geometry schema so
    callers can flexibly add points, lines, triangles, or axis-aligned boxes.
    """
    def __init__(self, classes: str | ValueMapLike | None, include_per_instance_label: bool = True, include_per_instance_confidence: bool = False, per_instance_schemas: dict[str, Schema] | None = None, **schema_kwargs: Any) -> None:
        """
        :param classes: Class map or a single class name for instance labels, or None to skip labels.
        :param include_per_instance_label: Whether to add a per-instance label.
        :param include_per_instance_confidence: Whether to add a per-instance confidence score.
        :param per_instance_schemas: Additional per-instance schemas.
        :param schema_kwargs: Additional keyword arguments forwarded to base `Schema`.
        """
