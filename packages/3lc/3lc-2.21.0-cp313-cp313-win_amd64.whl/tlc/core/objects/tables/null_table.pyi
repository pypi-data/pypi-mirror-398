from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class NullTable(Table):
    """A simple empty table"""
    def __init__(self, url: Url | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None: ...
    def __len__(self) -> int:
        """Get the number of rows in this table"""
