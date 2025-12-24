import numpy as np
from typing import TypedDict

class CocoRle(TypedDict):
    """A dictionary representation of a COCO RLE."""
    size: list[int]
    counts: bytes

class InstanceSegmentationDict(TypedDict):
    """The base class for dictionary representations of instance segmentation data."""
    image_height: int
    image_width: int
    instance_properties: dict[str, dict | list]

class SegmentationPolygonsDict(InstanceSegmentationDict):
    """A dictionary representation of instance segmentation data where each instance is represented by a list of
    polygons. Has the same keys as {class}`InstanceSegmentationDict` plus the key `polygons`.
    """
    polygons: list[list[float]]

class SegmentationMasksDict(InstanceSegmentationDict):
    """A dictionary representation of instance segmentation data where each instance is represented by a binary mask.
    Has the same keys as {class}`InstanceSegmentationDict` plus the key `masks`.
    """
    masks: np.ndarray[tuple[int, int, int], np.dtype[np.uint8]]

class _InternalInstanceSegmentationDict(TypedDict):
    """An internal dictionary representation of instance segmentation data."""
    image_height: int
    image_width: int
    instance_properties: dict[str, dict | list]
    rles: list[bytes]
