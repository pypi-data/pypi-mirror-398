from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.schema import DictValue as DictValue, Int32Value as Int32Value, Schema as Schema
from tlc.core.url import Url as Url
from typing import Any

class RandomTable(Table):
    """
    A table populated with random rows, as specified by a wanted row count
    and a Schema.

    The Schema allows for flexible configuration of the random rows, incl.:

    - Numeric value ranges
    - Categorical data
    - Fixed/variable length arrays
    - Nested structures
    """
    wanted_schema: Any
    wanted_row_count: int
    def __init__(self, *, url: Url | None = None, created: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, wanted_schema: Any = None, wanted_row_count: int | None = None, init_parameters: Any = None) -> None: ...
    def __len__(self) -> int:
        """Get the number of rows in this table"""
