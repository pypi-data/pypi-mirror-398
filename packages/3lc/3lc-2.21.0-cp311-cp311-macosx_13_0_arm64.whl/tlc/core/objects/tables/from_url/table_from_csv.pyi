from _typeshed import Incomplete
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.in_memory_rows_table import _InMemoryRowsTable
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

class TableFromCsv(_InMemoryRowsTable):
    '''A table populated from a comma-separated values (CSV) string loaded from a URL.

    This class represents a table that is loaded from a CSV file at the given URL. Its Schema is approximated as strings
    for all columns unless the property `override_table_rows_schema` is used, in which case:
     - the effective schema is modified with the given overrides, that may be "sparse"
     - the row-values are converted from str to a matching type which may not be exactly the override type, but should
       be compatible. Ie. if the override type is `Int32Value` and the value is `123` then the value will be converted
       to python type `int`

    :param url: URL of the table.
    :param created: Creation timestamp.
    :param row_cache_url: URL for row cache.
    :param row_cache_populated: Flag to indicate if the row cache is populated.
    :param override_table_rows_schema: Schema to override the default (naive) table rows schema.
    :param init_parameters: Initialization parameters for serialization.
    :param input_url: The input URL for the CSV data. This is required.

    :raises ValueError: if the input URL is not provided.
    '''
    input_url: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_url: Url | str | None = None, input_tables: list[Url] | None = None) -> None: ...
