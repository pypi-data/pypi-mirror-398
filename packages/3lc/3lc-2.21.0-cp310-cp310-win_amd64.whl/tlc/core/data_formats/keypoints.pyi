import numpy as np
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from tlc.core.builtins.constants.column_names import BBS_2D as BBS_2D, CONFIDENCE as CONFIDENCE, INSTANCES as INSTANCES, INSTANCES_ADDITIONAL_DATA as INSTANCES_ADDITIONAL_DATA, LABEL as LABEL, VERTICES_2D as VERTICES_2D, VERTICES_2D_ADDITIONAL_DATA as VERTICES_2D_ADDITIONAL_DATA, VISIBILITY as VISIBILITY, X_MAX as X_MAX, X_MIN as X_MIN, Y_MAX as Y_MAX, Y_MIN as Y_MIN
from tlc.core.helpers.keypoint_helper import KeypointHelper as KeypointHelper
from typing import Any

@dataclass
class Keypoints2DInstances:
    """A helper class for working with 2D keypoints instances in 3LC Tables.

    This class handles conversion to and from the internal dictionary representation of 2D keypoint instances,
    providing a convenient numpy-based interface for reading, manipulating, and writing keypoint data.

    Objects can be created in three ways:

    1. **Standard initialization**: Direct instantiation with numpy arrays
    2. **From table row**: Use `from_row()` to convert a 3LC Table row to numpy arrays
    3. **Build incrementally**: Use `create_empty()` and `add_instance()` to build up keypoint data

    :example:
    ```
    # Read from table row
    kpts = Keypoints2DInstances.from_row(table_row)
    print(kpts.keypoints.shape)  # (num_instances, num_keypoints, 2)

    # Build incrementally
    kpts = Keypoints2DInstances.create_empty(640, 480)
    kpts.add_instance(
        keypoints=[[100, 150], [120, 160], [140, 170]],
        bbox=[90, 140, 150, 180],
        label=0
    )

    # Write back to table
    updated_row = kpts.to_row()
    ```
    """
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    keypoints: np.ndarray[tuple[int, int, int], np.dtype[np.float32]]
    keypoint_visibilities: np.ndarray[tuple[int, int], np.dtype[np.int32]] | None
    keypoint_confidences: np.ndarray[tuple[int, int], np.dtype[np.float32]] | None
    instance_labels: np.ndarray[tuple[int], np.dtype[np.int32]] | None
    instance_confidences: np.ndarray[tuple[int], np.dtype[np.float32]] | None
    instance_bbs: np.ndarray[tuple[int, int, int, int], np.dtype[np.float32]] | None
    instance_extras: dict[str, np.ndarray]
    @property
    def image_width(self) -> float:
        """Convenience property: width of the coordinate system."""
    @property
    def image_height(self) -> float:
        """Convenience property: height of the coordinate system."""
    @classmethod
    def from_row(cls, row: Mapping[str, object]) -> Keypoints2DInstances:
        """Create a Keypoints2DInstances object from a 3LC Table row.

        Parses the hierarchical table row dictionary into structured numpy arrays for easier manipulation.
        Automatically detects whether per-keypoint visibility or confidence values are present.

        :param row: A dictionary representing a single row from a 3LC Table with keypoint data. Must contain
            the 'instances' key with a list of instance dictionaries, each containing 'vertices_2d' and 'bbs_2d'.
        :returns: A Keypoints2DInstances object with all keypoint data converted to numpy arrays.
        :raises ValueError: If the row does not contain instances, if both visibility and confidence are present,
            if visibility/confidence is only provided for a subset of instances, or if the number of
            labels doesn't match the number of instances.

        :example:
        ```
        table = tlc.Table.from_names(...)
        for row in table:
            kpts = Keypoints2DInstances.from_row(row)
            # Manipulate keypoint data
            kpts.keypoints[:, :, 0] *= scale_factor  # Scale x coordinates
            # Write back to table
            updated_row = kpts.to_row()
        ```
        """
    def to_row(self) -> dict[str, Any]:
        """Convert a Keypoints2DInstances object to the internal 3LC Table row format.

        Converts the numpy arrays back into the hierarchical dictionary structure expected by 3LC Tables.


        :returns: A dictionary with the structure expected by 3LC Tables, containing 'instances' and
            'instances_additional_data' keys.
        :raises ValueError: If both visibility and confidence arrays are present (only one is supported).

        :example:
        ```
        kpts = Keypoints2DInstances.from_row(row)
        # Modify keypoints
        kpts.keypoints[:, 0, :] += [10, 10]  # Shift first keypoint
        # Convert back to table format
        updated_row = kpts.to_row()
        ```
        """
    @classmethod
    def create_empty(cls, image_width: float | None = None, image_height: float | None = None, x_min: float = 0.0, y_min: float = 0.0, x_max: float | None = None, y_max: float | None = None, include_keypoint_confidences: bool = False, include_keypoint_visibilities: bool = False, include_instance_confidences: bool = False, include_instance_labels: bool = True, include_instance_bbs: bool = True, per_keypoint_extras_keys: Sequence[str] | None = None, instance_extras_keys: Sequence[str] | None = None) -> Keypoints2DInstances:
        """Create an empty Keypoints2DInstances object to build up incrementally.

        Useful for creating keypoint data from scratch by adding instances one at a time using `add_instance()`.
        Will contain labels and bounding boxes by default.

        :param x_min: Minimum x coordinate (default 0.0)
        :param y_min: Minimum y coordinate (default 0.0)
        :param x_max: Maximum x coordinate (provide this OR image_width)
        :param y_max: Maximum y coordinate (provide this OR image_height)
        :param image_width: Convenience parameter, sets x_max = x_min + image_width
        :param image_height: Convenience parameter, sets y_max = y_min + image_height
        :param include_keypoint_confidences: If True, initialize for storing per-keypoint confidence values.
            Mutually exclusive with include_keypoint_visibilities.
        :param include_keypoint_visibilities: If True, initialize for storing per-keypoint visibility values.
            Mutually exclusive with include_keypoint_confidences.
        :param include_instance_confidences: If True, initialize for storing per-instance confidence values.
        :param include_instance_labels: If True, initialize for storing per-instance label values. Default is True.
        :param include_instance_bbs: If True, initialize for storing per-instance bounding box values. Default is True.
        :param per_keypoint_extras_keys: Sequence of keys for additional per-keypoint attributes to initialize
        :param instance_extras_keys: Sequence of keys for additional per-instance attributes to initialize
        :returns: An empty Keypoints2DInstances object ready for adding instances.
        :raises ValueError: If bounds are not properly specified

        :example:
        ```
        kpts = Keypoints2DInstances.create_empty(
            image_width=640,
            image_height=480,
            include_keypoint_confidences=True
        )
        kpts.add_instance(
            keypoints=[[100, 150], [120, 160]],
            bbox=[90, 140, 130, 170],
            label=0,
            confidence=[0.9, 0.8]
        )
        ```
        """
    @property
    def instance_bbs_xywh(self) -> np.ndarray | None:
        """Return the instance bounding boxes in xywh format.

        Converts from the internal xyxy format [x_min, y_min, x_max, y_max] to xywh format
        [x_min, y_min, width, height], which is commonly used by some training frameworks.

        :returns: A numpy array of shape (num_instances, 4) with bounding boxes in [x, y, width, height] format,
            or None if no bounding boxes are present.
        """
    def add_instance(self, keypoints: list[float] | list[list[float]] | list[tuple[float, float]] | np.ndarray | None, bbox: list[float] | tuple[float, float, float, float] | np.ndarray | None = None, label: int | None = None, visibility: list[int] | np.ndarray | None = None, confidence: list[float] | np.ndarray | None = None, normalized: bool = False, bbox_format: str = 'xyxy', instance_confidence: float | None = None, instance_extras: Mapping[str, Any] | None = None) -> None:
        '''Add a single keypoint instance to the object.

        Adds one instance (e.g., one person, one object) with its keypoints, bounding box, and label.
        Keypoints can be provided in multiple formats and will be normalized internally.

        :param keypoints: Keypoint coordinates in one of these formats:
            - Flat list: [x1, y1, x2, y2, ...] or [x1, y1, v1, x2, y2, v2, ...]
            - List of pairs: [[x1, y1], [x2, y2], ...]
            - List of triplets: [[x1, y1, v1], [x2, y2, v2], ...] (visibility derived from 3rd value)
            - NumPy array of shape (K, 2) or (K, 3)
        :param bbox: Optional bounding box in xyxy format [x_min, y_min, x_max, y_max].
        :param label: Optional integer class label for this instance.
        :param visibility: Optional per-keypoint visibility flags (0=not labeled, 1=occluded, 2=visible).
            Mutually exclusive with confidence. If keypoints are provided with a 3rd column,
            that will be used as visibility unless explicitly overridden.
        :param confidence: Optional per-keypoint confidence scores. Mutually exclusive with visibility.
        :param normalized: Must be False. Normalized coordinates are not currently supported.
        :param bbox_format: Must be "xyxy". Other formats are not currently supported.
        :param instance_confidence: Optional confidence score for the entire instance.
        :param instance_extras: Optional dictionary of arbitrary per-instance attributes
            (e.g., {"track_id": 42, "area": 1500}). Values should be scalars. If an extra field is introduced
            after instances have been added, previous instances will be padded with NaN (float), -1 (int), or None
            (object).
        :raises ValueError: If keypoints are None, if both visibility and confidence are provided,
            if normalized=True or bbox_format!="xyxy", or if the number of keypoints doesn\'t match
            existing instances.

        :example:
        ```
        kpts = Keypoints2DInstances.create_empty(480, 640)
        # Add first instance with 3 keypoints
        kpts.add_instance(
            keypoints=[[100, 150], [120, 160], [140, 170]],
            bbox=[90, 140, 150, 180],
            label=0
        )
        # Add second instance (must also have 3 keypoints)
        kpts.add_instance(
            keypoints=[[200, 250, 2], [220, 260, 2], [240, 270, 1]],  # with visibility
            bbox=[190, 240, 250, 280],
            label=0
        )
        ```
        '''
    def __len__(self) -> int: ...
