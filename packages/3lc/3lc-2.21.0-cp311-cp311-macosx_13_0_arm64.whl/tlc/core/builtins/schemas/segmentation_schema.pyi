from tlc.client.sample_type import CategoricalLabel as CategoricalLabel, InstanceSegmentationPolygons as InstanceSegmentationPolygons
from tlc.core.builtins.constants.column_names import IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, INSTANCE_PROPERTIES as INSTANCE_PROPERTIES, IS_CROWD as IS_CROWD, LABEL as LABEL, RLES as RLES
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_LABEL as NUMBER_ROLE_LABEL
from tlc.core.schema import BoolValue as BoolValue, DimensionNumericValue as DimensionNumericValue, InstanceSegmentationRLEBytesStringValue as InstanceSegmentationRLEBytesStringValue, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema

class SegmentationSchema(Schema):
    """A schema for instance segmentation data that includes RLE-encoded masks and per-instance properties."""
    def __init__(self, label_value_map: dict[float, MapElement], display_name: str = '', description: str = '', sample_type: str = ..., relative: bool = False, writable: bool = True, include_iscrowd: bool = False, display_importance: float = 0) -> None: ...
