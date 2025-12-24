from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class RemixedTable(Table):
    '''
    A procedural table where rows are produced by remixing rows from an input
    table using a persisted ("pickled") Python code snippet.

    When needed, the table can also produce a remixed schema in the same manner,
    using a second code snippet.
    '''
    value_code_snippet: str | None
    schema_code_snippet: str | None
    def __init__(self, *, url: Url | None = None, created: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, value_code_snippet: str | None = None, schema_code_snippet: str | None = None, init_parameters: Any = None) -> None: ...
    def __len__(self) -> int:
        """Get the number of rows in this table"""
