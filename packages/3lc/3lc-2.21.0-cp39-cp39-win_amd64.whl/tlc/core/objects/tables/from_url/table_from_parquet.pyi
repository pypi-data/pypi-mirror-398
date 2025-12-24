from _typeshed import Incomplete
from tlc.core.builtins.constants.string_roles import STRING_ROLE_DATETIME as STRING_ROLE_DATETIME
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

logger: Incomplete

class TableFromParquet(_InMemoryColumnsTable):
    """A table populated from a Parquet file loaded from a URL"""
    input_url: Incomplete
    absolute_input_url: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_url: Url | str | None = None, input_tables: list[Url] | None = None) -> None: ...
    def is_all_parquet(self) -> bool:
        """
        This table is all Parquet.
        """
    def get_rows_as_binary(self, exclude_bulk_data: bool = False) -> bytes:
        """Return the table rows as binary data

        For TableFromParquet, if the data is produced without any transformation, it is possible to pass the input file.
        Otherwise the data normal binary production pipeline is used.
        """
    def get_row_cache_size(self) -> int:
        """Returns the size of the row cache in bytes.

        Returns the size of the row cache if it exists, otherwise returns the size of the input parquet file.
        """
