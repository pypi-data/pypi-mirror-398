from _typeshed import Incomplete
from abc import ABC
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class VirtualColumn(ABC):
    """
    Defines a single column within a VirtualColumnsAddedTable
    """
    schema_expression: Incomplete
    value_expression: Incomplete
    def __init__(self, schema_expression: str = '', value_expression: str = '') -> None: ...
    @staticmethod
    def schema() -> Schema:
        """
        Defines the schema for a single virtual column
        """

class VirtualColumnsAddedTable(Table):
    """
    A procedural table where an input table are augmented by virtual columns
    (i.e. virtual properties) according to user-configurable procedures.
    """
    virtual_columns: list[VirtualColumn] | None
    def __init__(self, *, url: Url | None = None, created: str | None = None, dataset_name: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool = False, virtual_columns: list[VirtualColumn] | None = None, init_parameters: Any = None) -> None: ...
    def __len__(self) -> int:
        """Get the number of rows in this table"""
