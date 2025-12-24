import pyarrow as pa
from _typeshed import Incomplete
from collections.abc import Mapping
from tlc.core.builtins.constants.string_roles import STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from typing import Any

logger: Incomplete

class _InMemoryColumnsTable(Table):
    """_InMemoryColumnsTable implements an in-memory table with efficient column access.

    ## Implementation notes for sub-classing

    Derived _InMemoryColumnsTable types can choose between two implementation paths:

    ## 1. Simple path

    Implement the column accessor _input_column and _input_len which allow the default _prepare_in_memory_columns to do
    the following (as pseudo code):

    ```
    for i in range(self._input_cols()):
        try:
            input_col = self._input_col(i)
            effective_col = self._get_effective_table_col(input_col)
            self._pa_table.append(effective_col)
    ```


    ## 2. Explicit iteration

    Implement free-form behavior by overriding _prepare_in_memory_columns and perform input data access and
    transformation. Make sure the store the final, transformed columns.

    In-memory preparation is triggered lazily by accessing data or explicitly by the ensure_data_production_is_ready
    method.
    """
    def __init__(self, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Mapping[str, object] | None = None, input_tables: list[Url] | None = None) -> None: ...
    def __len__(self) -> int: ...
    row_count: Incomplete
    def ensure_data_production_is_ready(self) -> None:
        """For an _InMemoryColsTable we produce the table columns in memory

        ## Data production path

        """
    def get_input_table(self) -> pa.Table: ...
    def get_column(self, name: str, combine_chunks: bool = True) -> pa.Array | pa.ChunkedArray: ...
