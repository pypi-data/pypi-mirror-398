from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import ImmutableDict as ImmutableDict, Table as Table, TableRow as TableRow
from tlc.core.objects.tables.in_memory_rows_table import _InMemoryRowsTable
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class RolledUpTable(_InMemoryRowsTable):
    """A table that is rolled up from another table.

    The rows of the rolled-up table are created by grouping the rows of the input table by the roll-up property.

    :param roll_up_property: The property to roll up.
    :param roll_up_columns: List of top-level columns that should be rolled up alongside the roll-up property.
    """
    input_table_url: ObjectReference
    roll_up_property: str
    roll_up_columns: list[str]
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, input_table_url: Url | Table | None = None, roll_up_property: str | None = None, roll_up_columns: list[str] | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None: ...
    @staticmethod
    def set_nested_value(row_data: dict[str, Any], path: str, value: Any) -> None: ...
    @staticmethod
    def get_nested_value_with_rollup_columns(row_data: dict[str, Any], roll_up_property: str, rollup_columns: list[str]) -> Any:
        """Returns the value of the roll-up property, with the roll-up columns added to the leaf node."""
