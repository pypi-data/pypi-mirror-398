from .bb_crop_interface import BBCropInterface as BBCropInterface
from typing import Any, TypedDict

SampleData = Any
MetricData = Any

class MetricTableInfo(TypedDict):
    """A dictionary containing summary metadata about a metric table."""
    url: str
    file_size: int
    stream_name: str
    row_count: int
