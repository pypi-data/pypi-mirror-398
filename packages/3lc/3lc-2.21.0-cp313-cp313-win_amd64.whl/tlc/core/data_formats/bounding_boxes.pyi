import abc
from _typeshed import Incomplete
from abc import abstractmethod
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_CENTER_X as NUMBER_ROLE_BB_CENTER_X, NUMBER_ROLE_BB_CENTER_Y as NUMBER_ROLE_BB_CENTER_Y, NUMBER_ROLE_BB_MAX_X as NUMBER_ROLE_BB_MAX_X, NUMBER_ROLE_BB_MAX_Y as NUMBER_ROLE_BB_MAX_Y, NUMBER_ROLE_BB_MIN_X as NUMBER_ROLE_BB_MIN_X, NUMBER_ROLE_BB_MIN_Y as NUMBER_ROLE_BB_MIN_Y, NUMBER_ROLE_BB_SIZE_X as NUMBER_ROLE_BB_SIZE_X, NUMBER_ROLE_BB_SIZE_Y as NUMBER_ROLE_BB_SIZE_Y
from tlc.core.builtins.constants.units import UNIT_RELATIVE as UNIT_RELATIVE
from tlc.core.schema import NumericValue as NumericValue, Schema as Schema
from typing import Callable

logger: Incomplete

class BoundingBox(list, metaclass=abc.ABCMeta):
    """The base class for all bounding boxes.

    The BoundingBox class aims to standardize the representation of bounding boxes across the codebase. It is a
    subclass of list, and represents a bounding box as a list of floats. The exact format of the list depends on the
    subclass, but the elements within the list are always floats which represent the parameters of the bounding box, in
    addition to a boolean attribute `normalized` which indicates whether the bounding box is normalized or not.

    The base BoundingBox class implements utility methods like `area`, `is_valid`, `normalize`, and `denormalize` by
    calling their definitions in the TopLeftXYWHBoundingBox subclass. Any other BoundingBox format
    must simply implement the `from_top_left_xywh` and `to_top_left_xywh` in order to get access to these utility
    methods.

    In many cases, needing to perform these conversions to and from TopLeftBoundingBox will not be the most
    efficient implementation of these methods. Where necessary, subclasses can override these methods to provide a more
    efficient implementation.
    """
    normalized: Incomplete
    def __init__(self, box: list[float], normalized: bool = False) -> None:
        """Initialize a BoundingBox.

        :param box: The list of floats representing the bounding box
        :param normalized: Whether the bounding box is normalized or not
        """
    @classmethod
    @abstractmethod
    def from_top_left_xywh(cls, box: TopLeftXYWHBoundingBox) -> BoundingBox:
        """Create a BoundingBox from a TopLeftXYWHBoundingBox. An abstract method which must be implemented by all
        subclasses.
        """
    @abstractmethod
    def to_top_left_xywh(self) -> TopLeftXYWHBoundingBox:
        """Create a TopLeftXYWHBoundingBox from this BoundingBox. An abstract method which must be implemented by all
        subclasses."""
    def area(self) -> float:
        """Compute the area of the bounding box by converting it to a TopLeftXYWHBoundingBox and calling its `area`
        method.

        :return: The area of the bounding box
        """
    def is_valid(self, image_width: int | None = None, image_height: int | None = None) -> bool:
        """Check if the bounding box is valid by converting it to a TopLeftXYWHBoundingBox and calling its `is_valid`
        method. The `image_width` and `image_height` parameters are required if and only if the bounding box is not
        normalized.

        :param image_width: The width of the image the bounding box is in
        :param image_height: The height of the image the bounding box is in
        :return: True if the bounding box is valid, False otherwise
        """
    def normalize(self, image_width: int, image_height: int) -> BoundingBox:
        """Normalize the bounding box by converting it to a TopLeftXYWHBoundingBox, calling its `normalize` method,
        and converting it back to the original format.

        :param image_width: The width of the image the bounding box is in
        :param image_height: The height of the image the bounding box is in
        :return: The normalized bounding box
        """
    def denormalize(self, image_width: int, image_height: int) -> BoundingBox:
        """Denormalize the bounding box by converting it to a TopLeftXYWHBoundingBox, calling its `denormalize` method,
        and converting it back to the original format.

        :param image_width: The width of the image the bounding box is in
        :param image_height: The height of the image the bounding box is in
        :return: The denormalized bounding box
        """
    @staticmethod
    def from_schema(schema: Schema) -> Callable[..., BoundingBox]:
        '''Return an BoundingBox-factory based on the provided schema.

        :param schema: The schema of the bounding box. Assumed to contain the following values: "x0", "x1", "y0", "y1".
        :returns: A callable which takes a list of floats and returns a BoundingBox.

        :Example:
        ```
        # Instantiate a BoundingBox subclass with the values [0, 0, 1, 1] given the schema `schema`.
        bounding_box = BoundingBox.from_schema(schema)([0, 0, 1, 1])
        ```
        '''

class XYWHBoundingBox(BoundingBox, metaclass=abc.ABCMeta):
    """An abstract class representing a bounding box as a list of floats in the format [x, y, w, h]

    Subclasses of XYWH can further specify whether x and y represent the top left corner of the bounding box or the
    center of the bounding box, whether w and h represent the full or the half width and height of the bounding box, and
    other variations.
    """

class TopLeftXYWHBoundingBox(XYWHBoundingBox):
    @classmethod
    def from_top_left_xywh(cls, box: TopLeftXYWHBoundingBox) -> TopLeftXYWHBoundingBox: ...
    def to_top_left_xywh(self) -> TopLeftXYWHBoundingBox: ...
    def area(self) -> float: ...
    normalized: bool
    def normalize(self, image_width: int, image_height: int) -> TopLeftXYWHBoundingBox: ...
    def denormalize(self, image_width: int, image_height: int) -> TopLeftXYWHBoundingBox: ...
    def snap_to(self, image_width: int, image_height: int, tol: float = ...) -> tuple[TopLeftXYWHBoundingBox, bool]: ...
    def remove_bounds_eps(self, image_width: int, image_height: int, tol: float = ...) -> TopLeftXYWHBoundingBox: ...
    def is_valid(self, image_width: int | None = None, image_height: int | None = None, tol: float = ...) -> bool: ...

class CenteredXYWHBoundingBox(XYWHBoundingBox):
    @classmethod
    def from_top_left_xywh(cls, box: TopLeftXYWHBoundingBox) -> CenteredXYWHBoundingBox: ...
    def to_top_left_xywh(self) -> TopLeftXYWHBoundingBox: ...

class XYXYBoundingBox(BoundingBox):
    @classmethod
    def from_top_left_xywh(cls, box: TopLeftXYWHBoundingBox) -> XYXYBoundingBox: ...
    def to_top_left_xywh(self) -> TopLeftXYWHBoundingBox: ...

class SegmentationBoundingBox(BoundingBox):
    @classmethod
    def from_top_left_xywh(cls, box: TopLeftXYWHBoundingBox) -> SegmentationBoundingBox: ...
    def to_top_left_xywh(self) -> TopLeftXYWHBoundingBox: ...
