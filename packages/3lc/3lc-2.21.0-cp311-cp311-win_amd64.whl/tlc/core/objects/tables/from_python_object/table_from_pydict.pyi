from collections.abc import Mapping
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import DictValue as DictValue, Schema as Schema
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

class TableFromPydict(_InMemoryColumnsTable):
    """A table populated from a Python dictionary

    The TableFromPydict will live in memory until persisted. When saved to Url it will write it's rows to a row cache
    file so that it can be loaded back into memory at a later time.

    :Example:
    ```
    python from tlc import TableFromPydict

    data = {
        'col_1': [3, 2, 1, 0], 'col_2': ['a', 'b', 'c', 'd']
    }
    table = TableFromPydict(data=data)
    ```
    """
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, data: Mapping[str, object] | None = None, input_tables: list[Url] | None = None) -> None: ...
