from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion_factory import create_optional_filter as create_optional_filter
from tlc.core.objects.tables.in_memory_rows_table import SkipRow as SkipRow, _InMemoryRowsTable
from tlc.core.schema import DictValue as DictValue, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class FilteredTable(_InMemoryRowsTable):
    """
    A procedural table where rows in an input table have been filtered
    according to the assigned filter criterion which can be any combination of

    - A free-text search string (matching all string properties)
    - Per-property filters (e.g. in-numeric-range, must-contain-string,
      boolean match,...)
    - Paint operations (i.e. sequences of inside/outside tests in 2D space/
      projected 3D space)

    """
    input_table_url: ObjectReference
    filter_criterion: FilterCriterion | None
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Schema | None = None, input_table_url: Url | Table | None = None, filter_criterion: FilterCriterion | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None: ...
