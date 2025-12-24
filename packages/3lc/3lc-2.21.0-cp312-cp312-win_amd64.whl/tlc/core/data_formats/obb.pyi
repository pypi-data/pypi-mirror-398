import numpy as np
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from tlc.core.builtins.constants.column_names import CENTER_X as CENTER_X, CENTER_Y as CENTER_Y, CENTER_Z as CENTER_Z, CONFIDENCE as CONFIDENCE, INSTANCES as INSTANCES, INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, LABEL as LABEL, ORIENTED_BBS_2D as ORIENTED_BBS_2D, ORIENTED_BBS_3D as ORIENTED_BBS_3D, PITCH as PITCH, ROLL as ROLL, ROTATION as ROTATION, SIZE_X as SIZE_X, SIZE_Y as SIZE_Y, SIZE_Z as SIZE_Z, X_MAX as X_MAX, X_MIN as X_MIN, YAW as YAW, Y_MAX as Y_MAX, Y_MIN as Y_MIN, Z_MAX as Z_MAX, Z_MIN as Z_MIN
from typing import Any

@dataclass
class OBB2DInstances:
    """A helper class for working with Oriented Bounding Box (OBB) instances in 3LC Tables.

    This class handles conversion to and from the internal dictionary representation of OBB instances,
    providing a convenient numpy-based interface for reading, manipulating, and writing OBB data.

    Objects can be created in three ways:

    1. **Standard initialization**: Direct instantiation with numpy arrays
    2. **From table row**: Use `from_row()` to convert a 3LC Table row to numpy arrays
    3. **Build incrementally**: Use `create_empty()` and `add_instance()` to build up OBB data

    :example:
    ```
    # Read from table row
    obbs = OBB2DInstances.from_row(table_row)
    print(obbs.obbs.shape)  # (num_instances, 5)

    # Build incrementally
    obbs = OBB2DInstances.create_empty(640, 480)
    obbs.add_instance(
        obb=[320, 240, 100, 50, 0.785],  # center_x, center_y, width, height, rotation
        label=0,
        confidence=0.95
    )

    # Write back to table
    updated_row = obbs.to_row()
    ```
    """
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    obbs: np.ndarray[tuple[int, int], np.dtype[np.float32]]
    instance_labels: np.ndarray[tuple[int], np.dtype[np.int32]] | None
    instance_confidences: np.ndarray | None
    instance_extras: dict[str, np.ndarray]
    @property
    def image_width(self) -> float:
        """Convenience property: width of the coordinate system."""
    @property
    def image_height(self) -> float:
        """Convenience property: height of the coordinate system."""
    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> OBB2DInstances:
        """Create an OBB2DInstances object from a 3LC Table row.

        Parses the hierarchical table row dictionary into structured numpy arrays for easier manipulation.

        :param row: A dictionary representing a single row from a 3LC Table with OBB data. Must contain
            the 'instances' key with a list of instance dictionaries, each containing an 'oriented_bbs_2d'
            entry with 'center_x', 'center_y', 'width', 'height', and 'rotation' keys.
        :returns: An OBB2DInstances object with all OBB data converted to numpy arrays.
        :raises ValueError: If the row does not contain instances or if the number of labels doesn't match
            the number of instances.

        :example:
        ```
        table = tlc.Table.from_names(...)
        for row in table:
            obbs = OBB2DInstances.from_row(row)
            # Manipulate OBB data
            obbs.obbs[:, 4] += 0.1  # Rotate all boxes by 0.1 radians
            # Write back to table
            updated_row = obbs.to_row()
        ```
        """
    def to_row(self) -> dict[str, Any]:
        """Convert an OBB2DInstances object to the internal 3LC Table row format.

        Converts the numpy arrays back into the hierarchical dictionary structure expected by 3LC Tables.

        :returns: A dictionary with the structure expected by 3LC Tables, containing 'instances' and
            'instances_additional_data' keys.

        :example:
        ```
        obbs = OBB2DInstances.from_row(row)
        # Modify OBBs
        obbs.obbs[:, :2] += [10, 10]  # Shift all centers by (10, 10)
        # Convert back to table format
        updated_row = obbs.to_row()
        ```
        """
    @classmethod
    def create_empty(cls, image_width: float | None = None, image_height: float | None = None, x_min: float = 0.0, y_min: float = 0.0, x_max: float | None = None, y_max: float | None = None, include_instance_labels: bool = True, include_instance_confidences: bool = False, instance_extras_keys: Sequence[str] | None = None) -> OBB2DInstances:
        '''Create an empty OBB2DInstances object to build up incrementally.

        Useful for creating OBB data from scratch by adding instances one at a time using `add_instance()`.

        :param x_min: Minimum x coordinate (default 0.0)
        :param y_min: Minimum y coordinate (default 0.0)
        :param x_max: Maximum x coordinate (provide this OR image_width)
        :param y_max: Maximum y coordinate (provide this OR image_height)
        :param image_width: Convenience parameter, sets x_max = x_min + image_width
        :param image_height: Convenience parameter, sets y_max = y_min + image_height
        :param include_instance_labels: If True, initialize for storing per-instance labels
        :param include_instance_confidences: If True, initialize for storing per-instance confidence values
        :param instance_extras_keys: Sequence of keys for additional per-instance attributes to initialize
        :returns: An empty OBB2DInstances object ready for adding instances.
        :raises ValueError: If bounds are not properly specified

        :example:
        ```
        obbs = OBB2DInstances.create_empty(
            image_width=640,
            image_height=480,
            instance_extras_keys=["track_id", "quality_score"]
        )
        obbs.add_instance(
            obb=[320, 240, 100, 50, 0.785],
            label=0,
            confidence=0.95,
            instance_extras={"track_id": 42, "quality_score": 0.87}
        )
        ```
        '''
    def add_instance(self, obb: list[float] | tuple[float, float, float, float, float] | np.ndarray, label: int | None = None, confidence: float | None = None, instance_extras: Mapping[str, Any] | None = None) -> None:
        '''Add a single oriented bounding box instance to the object.

        :param obb: Oriented bounding box in the format [x_center, y_center, width, height, rotation].
            Rotation should be in radians in the range [0, pi/2). Can be provided as a list, tuple, or numpy array.
        :param label: Optional integer class label for this instance.
        :param confidence: Optional confidence score for this instance.
        :param instance_extras: Optional dictionary of arbitrary per-instance attributes
            (e.g., {"track_id": 42, "area": 1500}). Values should be scalars. If an extra field is introduced
            after instances have been added, previous instances will be padded with NaN (float), -1 (int), or None
            (object).
        :raises ValueError: If the OBB does not have exactly 5 elements.

        :example:
        ```
        obbs = OBB2DInstances.create_empty(image_width=640, image_height=480)
        obbs.add_instance(
            obb=[320, 240, 100, 50, 0.785],  # 45 degrees
            label=0,
            confidence=0.95
        )
        obbs.add_instance(
            obb=[200, 150, 80, 60, 1.571],  # 90 degrees
            label=1,
            confidence=0.88
        )
        ```
        '''
    def __len__(self) -> int: ...

@dataclass
class OBB3DInstances:
    """Helper class for working with 3D Oriented Bounding Box (OBB) instances in 3LC Tables.

    Representation per instance: [center_x, center_y, center_z, size_x, size_y, size_z, yaw, pitch, roll].
    """
    x_min: float
    y_min: float
    z_min: float
    x_max: float
    y_max: float
    z_max: float
    obbs: np.ndarray[tuple[int, int], np.dtype[np.float32]]
    instance_labels: np.ndarray[tuple[int], np.dtype[np.int32]] | None
    instance_confidences: np.ndarray | None
    instance_extras: dict[str, np.ndarray]
    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> OBB3DInstances:
        """Create an OBB3DInstances object from a 3LC Table row.

        Expects bounding box data under `instances.oriented_bbs_3d` with keys
        `center_x`, `center_y`, `center_z`, `size_x`, `size_y`, `size_z`, `yaw`, `pitch`, `roll`.
        """
    def to_row(self) -> dict[str, Any]:
        """Convert an OBB3DInstances object to the internal 3LC Table row format."""
    @classmethod
    def create_empty(cls, x_min: float = 0.0, y_min: float = 0.0, z_min: float = 0.0, x_max: float = 0.0, y_max: float = 0.0, z_max: float = 0.0, include_instance_labels: bool = True, include_instance_confidences: bool = False, instance_extras_keys: Sequence[str] | None = None) -> OBB3DInstances:
        """Create an empty OBB3DInstances object to build up incrementally.

        Provide either x_max/y_max/z_max or volume_width/height/depth for each axis.
        """
    def add_instance(self, obb: list[float] | tuple[float, float, float, float, float, float, float, float, float] | np.ndarray, label: int | None = None, confidence: float | None = None, instance_extras: Mapping[str, Any] | None = None) -> None:
        """Add a single 3D oriented bounding box instance.

        `obb` must be [cx, cy, cz, sx, sy, sz, yaw, pitch, roll].
        """
    def __len__(self) -> int: ...
