from _typeshed import Incomplete
from tlc.core.builtins.constants.display_importances import DISPLAY_IMPORTANCE_TABLE_URLS as DISPLAY_IMPORTANCE_TABLE_URLS
from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.builtins.schemas.row_count_schema import row_count_schema as row_count_schema
from tlc.core.object import Object as Object
from tlc.core.objects.table import Table as Table
from tlc.core.schema import DatetimeStringValue as DatetimeStringValue, DimensionNumericValue as DimensionNumericValue, Schema as Schema, StringValue as StringValue, UrlStringValue as UrlStringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from typing import Any

class TableInfo:
    """
    Information about a table (but not a table itself).

    This only includes properties which are common across different table types.
    """
    url: Incomplete
    created: Incomplete
    input_table_urls: Incomplete
    row_count: Incomplete
    dataset_name: Incomplete
    project_name: Incomplete
    is_url_writable: Incomplete
    description: Incomplete
    type: Incomplete
    row_cache_url: Incomplete
    def __init__(self, url: Url, created: str, input_table_urls: list[Url], row_count: int, dataset_name: str = '', project_name: str = '', is_url_writable: bool = False, description: str = '', object_type: str = '', row_cache_url: str = '') -> None: ...
    @staticmethod
    def add_table_info_properties_to_schema(schema: Schema) -> None:
        """
        Adds the properties for a TableInfo to a schema
        """
    def get(self, attr_name: str, default: Any = None) -> Any | None:
        """
        Allows dictionary-like access to attributes.
        Returns the attribute value if it exists, else returns the default value.
        """
    @staticmethod
    def from_table(table: Table) -> TableInfo:
        """Creates a TableInfo object from a Table object"""
