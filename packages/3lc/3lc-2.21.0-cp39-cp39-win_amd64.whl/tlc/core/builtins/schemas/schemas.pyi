from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import EXAMPLE_ID as EXAMPLE_ID
from tlc.core.builtins.constants.display_importances import DISPLAY_IMPORTANCE_EPOCH as DISPLAY_IMPORTANCE_EPOCH, DISPLAY_IMPORTANCE_INPUT_TABLE_ID as DISPLAY_IMPORTANCE_INPUT_TABLE_ID, DISPLAY_IMPORTANCE_ITERATION as DISPLAY_IMPORTANCE_ITERATION
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_FOREIGN_KEY as NUMBER_ROLE_FOREIGN_KEY, NUMBER_ROLE_LABEL as NUMBER_ROLE_LABEL, NUMBER_ROLE_RGB_COMPONENT_BLUE as NUMBER_ROLE_RGB_COMPONENT_BLUE, NUMBER_ROLE_RGB_COMPONENT_GREEN as NUMBER_ROLE_RGB_COMPONENT_GREEN, NUMBER_ROLE_RGB_COMPONENT_RED as NUMBER_ROLE_RGB_COMPONENT_RED, NUMBER_ROLE_SAMPLE_WEIGHT as NUMBER_ROLE_SAMPLE_WEIGHT, NUMBER_ROLE_TEMPORAL_INDEX as NUMBER_ROLE_TEMPORAL_INDEX, NUMBER_ROLE_XYZ_COMPONENT as NUMBER_ROLE_XYZ_COMPONENT, NUMBER_ROLE_XY_COMPONENT as NUMBER_ROLE_XY_COMPONENT
from tlc.core.schema import BoolValue as BoolValue, DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, ImageUrlStringValue as ImageUrlStringValue, Int32Value as Int32Value, MapElement as MapElement, NumericValue as NumericValue, Schema as Schema, StringValue as StringValue, Uint8Value as Uint8Value, ValueMapLike as ValueMapLike
from typing import Any, Literal

class RedComponentSchema(Schema):
    """A schema for a red component (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class RedComponentListSchema(RedComponentSchema):
    """A schema for a list of red components (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class GreenComponentSchema(Schema):
    """A schema for a green component (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class GreenComponentListSchema(GreenComponentSchema):
    """A schema for a list of green components (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class BlueComponentSchema(Schema):
    """A schema for a blue component (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class BlueComponentListSchema(BlueComponentSchema):
    """A schema for a list of blue components (uint8 in range 0-255)"""
    def __init__(self, **kwargs: Any) -> None: ...

class Float32Schema(Schema):
    """A schema for a float32 value"""
    def __init__(self, number_role: str = '', **kwargs: Any) -> None:
        """
        :param number_role: The role of the float32 value.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class Float32ListSchema(Float32Schema):
    """A schema for a list of float32 values"""
    size0: Incomplete
    def __init__(self, list_size: int | None = None, number_role: str = '', **kwargs: Any) -> None:
        """
        :param list_size: The size of the list, if fixed-size. If None, the list can be of any size.
        :param number_role: The role of the number values in the list.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class Int32Schema(Schema):
    """A schema for an int32 value"""
    def __init__(self, number_role: str = '', **kwargs: Any) -> None:
        """
        :param number_role: The role of the int32 value.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class Int32ListSchema(Int32Schema):
    """A schema for a list of int32 values"""
    size0: Incomplete
    def __init__(self, list_size: int | None = None, number_role: str = '', **kwargs: Any) -> None:
        """
        :param list_size: The size of the list, if fixed-size. If None, the list can be of any size.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class BoolSchema(Schema):
    """A schema for a boolean value"""
    def __init__(self, **kwargs: Any) -> None:
        """
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class BoolListSchema(BoolSchema):
    """A schema for a list of boolean values"""
    size0: Incomplete
    def __init__(self, list_size: int | None = None, **kwargs: Any) -> None:
        """
        :param list_size: The size of the list, if fixed-size. If None, the list can be of any size.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class StringSchema(Schema):
    """A schema for a string value"""
    def __init__(self, string_role: str = '', **kwargs: Any) -> None:
        """
        :param string_role: The role of the string value.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class StringListSchema(StringSchema):
    """A schema for a list of string values"""
    size0: Incomplete
    def __init__(self, list_size: int | None = None, **kwargs: Any) -> None:
        """
        :param list_size: The size of the list, if fixed-size. If None, the list can be of any size.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class ImageUrlSchema(Schema):
    """A schema for an image URL"""
    def __init__(self, **kwargs: Any) -> None: ...

class XyzSchema(Schema):
    """A Schema defining an (x, y, z) value"""
    composite_role: Incomplete
    def __init__(self, display_name: str = '', description: str = '', writable: bool = True, display_importance: float = 0, value_type: str = ...) -> None: ...

class COCOLabelSchema(Schema):
    """
    A Schema defining COCO label
    """
    value: Incomplete
    def __init__(self, display_name: str = 'label', description: str = 'COCO Label', writable: bool = False, display_importance: float = 0) -> None: ...

class CIFAR10LabelSchema(Schema):
    """
    A Schema defining CIFAR10 label
    """
    value: Incomplete
    def __init__(self, display_name: str = 'label', description: str = 'CIFAR-10 Label', writable: bool = False, display_importance: float = 0, value_type: str = ...) -> None: ...

class CategoricalLabelSchema(Schema):
    """A schema for a categorical label"""
    value: Incomplete
    def __init__(self, class_names: list[str] | None = None, classes: ValueMapLike | None = None, **kwargs: Any) -> None:
        """
        :param class_names: Deprecated, use classes instead
        :param classes: The classes to use for the label. If a list or sequence, each item will be converted to a
            MapElement and assigned a zero-based integer key. If a dict, the keys will be used as the label values and
            the values will be converted to MapElements.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class CategoricalLabelListSchema(CategoricalLabelSchema):
    """A schema for a list of categorical labels"""
    size0: Incomplete
    def __init__(self, classes: ValueMapLike | None = None, class_names: list[str] | None = None, list_size: int | None = None, **kwargs: Any) -> None:
        """
        :param classes: The classes to use for the label
        :param class_names: Deprecated, use classes instead
        :param list_size: The size of the list, if fixed-size. If None, the list can be of any size.
        :param kwargs: Additional arguments to pass to the Schema constructor
        """

class FloatVector2Schema(Schema):
    """A schema for a 2D vector"""
    value: Incomplete
    size0: Incomplete
    def __init__(self, display_name: str = '2D Embedding', description: str = '', writable: bool = False, display_importance: float = 0, number_role: str = ..., mode: Literal['numpy', 'python'] = 'python') -> None: ...

class FloatVector3Schema(Schema):
    """A schema for a 3D vector"""
    value: Incomplete
    size0: Incomplete
    def __init__(self, display_name: str = '3D Embedding', description: str = '', writable: bool = False, display_importance: float = 0, number_role: str = ..., mode: Literal['numpy', 'python'] = 'python') -> None: ...

class ExampleIdSchema(Schema):
    """A schema for example ID values

    Example ID is a unique identifier for an example. It is used to identify
    examples across different tables.
    """
    value: Incomplete
    def __init__(self, display_name: str = 'Example ID', description: str = '', writable: bool = False, computable: bool = False) -> None: ...

class EpochSchema(Schema):
    """A schema for epoch values"""
    def __init__(self, display_name: str = 'Epoch', description: str = 'Epoch of training', display_importance: float | None = None) -> None: ...

class IterationSchema(Schema):
    """A schema for iteration values"""
    def __init__(self, display_name: str = 'Iteration', description: str = 'The current iteration of the training process.', display_importance: float | None = None) -> None: ...

class ForeignTableIdSchema(Schema):
    """A schema describing a value that identifies a foreign table"""
    def __init__(self, foreign_table_url: str, display_name: str = '') -> None: ...

class SampleWeightSchema(Schema):
    """A schema for sample weight values"""
    def __init__(self, display_name: str = 'Weight', description: str = 'The weights of the samples in this table.', sample_type: str = 'hidden', default_value: float = 1.0) -> None:
        """Initialize the SampleWeightSchema

        :param display_name: The display name of the schema
        :param description: The description of the schema
        :param sample_type: The sample type of the schema
        :param default_value: The default value of the schema
        """
