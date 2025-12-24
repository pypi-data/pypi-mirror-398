import pyarrow as pa
from _typeshed import Incomplete
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_NN_EMBEDDING as NUMBER_ROLE_NN_EMBEDDING
from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.helpers.bulk_data_helper import BulkDataHelper as BulkDataHelper, CODEBOOK_PROPERTY_SUFFIX as CODEBOOK_PROPERTY_SUFFIX
from tlc.core.schema import BoolValue as BoolValue, BytesStringValue as BytesStringValue, DatetimeStringValue as DatetimeStringValue, DictValue as DictValue, DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Float64Value as Float64Value, ImageUrlStringValue as ImageUrlStringValue, InstanceSegmentationRLEBytesStringValue as InstanceSegmentationRLEBytesStringValue, Int16Value as Int16Value, Int32Value as Int32Value, Int64Value as Int64Value, Int8Value as Int8Value, MapElement as MapElement, NumericValue as NumericValue, ScalarValue as ScalarValue, Schema as Schema, SegmentationMaskUrlStringValue as SegmentationMaskUrlStringValue, SegmentationUrlStringValue as SegmentationUrlStringValue, StringValue as StringValue, TensorUrlStringValue as TensorUrlStringValue, TimestampValue as TimestampValue, Uint16Value as Uint16Value, Uint32Value as Uint32Value, Uint64Value as Uint64Value, Uint8Value as Uint8Value, UrlStringValue as UrlStringValue
from tlc.core.url import Url as Url
from typing import Any, ClassVar, Literal

logger: Incomplete

class SchemaHelper:
    """A class with helper methods for working with Schema objects"""
    ARROW_TYPE_TO_SCALAR_VALUE_MAPPING: ClassVar
    SCALAR_VALUE_TYPE_TO_ARROW_TYPE_MAPPING: ClassVar
    @staticmethod
    def object_input_urls(obj: Any, schema: Schema) -> list[Url]:
        """
        Returns a list of all URLs referenced by this object, from scalar
        strings or lists of strings

        Note: the result is likely to be relative with respect to the object's URL
        """
    @staticmethod
    def from_pyarrow_datatype(data_type: pa.DataType) -> ScalarValue | None:
        """Converts a DataType to a ScalarValue.

        :param data_type: The pyarrow DataType object to convert.
        :returns: The type of the scalar value that corresponds to the pyarrow DataType.
        """
    @staticmethod
    def scalar_value_to_pyarrow_datatype(value: ScalarValue) -> pa.DataType:
        """Converts a ScalarValue to a pyarrow DataType.

        :param value: The scalar value to convert.
        :returns: The corresponding pyarrow datatype.
        """
    @staticmethod
    def to_pyarrow_datatype(schema_or_value: Schema | ScalarValue) -> pa.DataType:
        """Converts a Schema or ScalarValue to a pyarrow DataType.

        Currently supports scalar types, lists of scalar types, structs, and lists of structs.

        :param schema_or_value: The schema or scalar value to convert.
        :returns: The corresponding pyarrow datatype.
        """
    @staticmethod
    def tlc_schema_to_pyarrow_schema(tlc_schema: Schema) -> pa.Schema:
        """Convert a 3LC schema to a PyArrow schema.

        :param tlc_schema: The 3LC schema to convert.
        :returns: The PyArrow schema.
        """
    @staticmethod
    def find_pyarrow_types(arrow_schema: pa.Schema, scalar_types: list[pa.DataType]) -> list[dict[str, object]]:
        """Find all the paths in an Arrow schema that correspond to scalar types."""
    @staticmethod
    def pyarrow_list_to_tlc_schema(list_type: pa.ListType | pa.FixedSizeListType, **schema_kwargs: Any) -> Schema: ...
    @staticmethod
    def pyarrow_schema_to_tlc_schema(arrow_schema: pa.Schema, **schema_kwargs: Any) -> Schema:
        """Convert a PyArrow schema to a 3LC schema.

        :param arrow_schema: The PyArrow schema to convert.
        :param schema_kwargs: Additional keyword arguments to pass to the Schema constructor.
        :returns: The 3LC schema.
        """
    @staticmethod
    def cast_scalar(value: Any, value_type: ScalarValue) -> Any:
        """Cast a value which is a ScalarValue into its corresponding python type."""
    @staticmethod
    def cast_value(value: Any, value_schema: Schema, on_error: Literal['raise', 'discard'] = 'raise') -> Any:
        """Cast any value into its corresponding python type based on the Schema."""
    @staticmethod
    def default_scalar(value_type: ScalarValue) -> Any:
        """Returns the default value for a ScalarValue."""
    @staticmethod
    def default_value(schema: Schema) -> Any:
        """Returns the default value for a schema.

        A schema holds either:
          - a ScalarValue (schema.value) which corresponds to a scalar type (potentially an array of scalars)
          - a dict of sub-Schemas (schema.values) corresponding compound types (potentially an array)

        """
    @staticmethod
    def is_computable(schema: Schema) -> bool:
        """Returns True if the schema is computable."""
    @staticmethod
    def add_schema_to_existing_schema_at_location(added_schema: Schema, existing_schema: Schema, location: list[str]) -> None:
        """Adds the value to the schema at the given location."""
    @staticmethod
    def is_pseudo_scalar(schema: Schema) -> bool:
        """Returns True if the schema is a pseudo-scalar.

        When a schema has a size0 with min=1 and max=1, it is considered a pseudo-scalar. This is a trick we use when
        unrolling/rolling up tables. We want to treat table cells with 1-element lists as scalars.
        """
    @staticmethod
    def get_nested_schema(schema: Schema, path: str) -> Schema | None:
        """Retrieves a nested schema from a schema.

        :param schema: The schema to retrieve the nested schema from.
        :param path: The (dot-separated) path to the nested schema.
        :return: The nested schema, or None if the path doesn't exist.
        """
    @staticmethod
    def set_nested_schema(schema: Schema, path: str, value: Schema) -> None:
        """Sets a nested schema in a schema.
        :param schema: The schema to set the nested schema in.
        :param path: The (dot-separated) path to the nested schema.
        :param value: The value to set the nested schema to.
        :raises ValueError: If the path to the schema does not exist or if the leaf node already exists.
        """
    @staticmethod
    def declare_bulk_data_columns(schema: Schema, columns: list[str]) -> None:
        """Declares a list of columns as bulk data columns.
        :param schema: The schema to declare the bulk data columns in.
        :param columns: The list of columns to declare as bulk data columns.
        """
    @staticmethod
    def get_bulk_data_values(schema: Schema, path: list[str] | None = None) -> list[str]:
        """Returns a list of bulk data values from a schema.
        :param schema: The schema to get the bulk data values from.
        :return: A list dot-separated paths to leaf schemas that are bulk data.
        """
    @staticmethod
    def create_sparse_schema_from_scalar_value(path: str, scalar_value: ScalarValue) -> Schema:
        """Creates a sparse schema from a path and a schema.

        :param path: The (dot-separated) path to the nested schema.
        :param new_schema: The schema to create the sparse schema from.
        :return: The sparse schema.
        """
    @staticmethod
    def create_sparse_schema_from_schema(path: str, schema: Schema) -> Schema:
        """Creates a sparse schema from a path and a schema.

        :param path: The (dot-separated) path to the nested schema.
        :param new_schema: The schema to create the sparse schema from.
        :return: The sparse schema.
        """
    @staticmethod
    def top_level_url_values(schema: Schema) -> list[str]:
        """Return a list of sub-schemas that represent atomic URL values.

        This function does not return the keys of nested URL values.
        :param schema: The schema to retrieve the URL values from.
        :return: A list of sub-value keys corresponding to URL values.
        """
    @staticmethod
    def nested_url_columns(schema: Schema, column_path_to_here: list[str] | None = None) -> list[list[str]]:
        """Get columns from the schema that have string roles URL/X. Each column is represented as a list of strings,
        with subsequent strings denoting nested columns.

        :param schema: The schema to retrieve the URL columns from.
        :param column_path_to_here: The path to the current schema.
        """
    @staticmethod
    def is_embedding_value(schema: Schema) -> bool:
        """Returns True if the schema is an atomic schema describing an unreduced embedding value."""
    @staticmethod
    def is_numeric_value(schema: Schema) -> bool:
        """Returns True if the schema is an atomic schema describing a numeric value."""
    @staticmethod
    def to_simple_value_map(value_map: dict[float, MapElement]) -> dict[int, str]:
        """Converts a value map with float keys and MapElement values to a map with int keys and str values"""
    @staticmethod
    def populate_default_values(row_data: Any, row_schema: Schema) -> Any:
        """Recursively populate default values according to `row_schema`."""
