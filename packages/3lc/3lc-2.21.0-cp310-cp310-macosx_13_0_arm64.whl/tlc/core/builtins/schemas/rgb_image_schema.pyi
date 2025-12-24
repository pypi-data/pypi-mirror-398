from tlc.core.builtins.constants.column_names import PIXELS as PIXELS
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_PIXEL_COUNT as NUMBER_ROLE_PIXEL_COUNT, NUMBER_ROLE_RGB_COMPONENT as NUMBER_ROLE_RGB_COMPONENT
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, MapElement as MapElement, Schema as Schema, Uint8Value as Uint8Value

def rgb_image_schema(image_width: int = -1, image_height: int = -1) -> Schema:
    """
    Returns a standard schema describing an RGB image
    """
