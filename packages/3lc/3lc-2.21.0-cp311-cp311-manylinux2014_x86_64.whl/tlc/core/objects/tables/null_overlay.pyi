from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.objects.tables.from_table.schema_helper import input_table_schema as input_table_schema
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from typing import Any

class NullOverlay(Table):
    """A simple empty overlay table that returns its input table's items as its own"""
    input_table_url: ObjectReference
    def __init__(self, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_table_url: Url | Table | None = None, input_tables: list[Url] | None = None) -> None: ...
    def __len__(self) -> int: ...
