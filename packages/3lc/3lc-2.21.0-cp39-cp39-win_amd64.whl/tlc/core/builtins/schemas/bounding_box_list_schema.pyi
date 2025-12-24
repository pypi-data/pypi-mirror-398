from tlc.core.builtins.constants.column_names import BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, CONFIDENCE as CONFIDENCE, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, IOU as IOU, IS_CROWD as IS_CROWD, LABEL as LABEL, SEGMENTATION as SEGMENTATION, X0 as X0, X1 as X1, Y0 as Y0, Y1 as Y1
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_BB_MAX_X as NUMBER_ROLE_BB_MAX_X, NUMBER_ROLE_BB_MAX_Y as NUMBER_ROLE_BB_MAX_Y, NUMBER_ROLE_BB_MIN_X as NUMBER_ROLE_BB_MIN_X, NUMBER_ROLE_BB_MIN_Y as NUMBER_ROLE_BB_MIN_Y, NUMBER_ROLE_CONFIDENCE as NUMBER_ROLE_CONFIDENCE, NUMBER_ROLE_IOU as NUMBER_ROLE_IOU, NUMBER_ROLE_LABEL as NUMBER_ROLE_LABEL
from tlc.core.builtins.constants.values import DEFAULT_BB_MAX_COUNT as DEFAULT_BB_MAX_COUNT
from tlc.core.schema import BoolValue as BoolValue, DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema

class BoundingBoxListSchema(Schema):
    """A schema for a COCO-like bounding box list"""
    def __init__(self, label_value_map: dict[float, MapElement], x0_number_role: str = ..., x1_number_role: str = ..., y0_number_role: str = ..., y1_number_role: str = ..., x0_unit: str = '', x1_unit: str = '', y0_unit: str = '', y1_unit: str = '', display_name: str = '', description: str = '', writable: bool = True, display_importance: float = 0, is_prediction: bool = False, include_segmentation: bool = True, include_iscrowd: bool = False, include_confidence: bool | None = None, include_iou: bool | None = None) -> None: ...
