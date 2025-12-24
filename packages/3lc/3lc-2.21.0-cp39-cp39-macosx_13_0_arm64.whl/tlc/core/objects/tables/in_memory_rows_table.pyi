from _typeshed import Incomplete
from collections.abc import Mapping
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class SkipRow(Exception): ...

class _InMemoryRowsTable(Table):
    """InMemoryRowsTable implements an in memory table with efficient row access.

    ## Implementation notes for sub-classing

    Derived _InMemoryRowsTable types can chose between two implementation paths:

    ## 1. Simple path

    Implement the row accessor _input_row and _input_len to allow the default _prepare_in_memory_rows to do the
    following (as pseudo code):

    ```
    for i in range(self._input_len()):
        try:
            input_row = self._input_row(i)
            effective_row = self._get_effective_table_row(row_data=input_row, row_index=i)
            self._in_memory_rows.append(effective_row)
            output_row_index += 1
        except SkipRow:
            pass
    ```

    Raise the SkipRow exception inside _input_row in order to omit or filter input rows.

    ## 2. Explicit iteration

    Implement free form behavior by overriding _prepare_in_memory_rows and perform input data access and transformation.
    Make sure the store the final, transformed row items.

    In memory preparation is triggered lazily by accessing data or explicitly by the ensure_data_production_is_ready
    method.
    """
    def __init__(self, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Mapping[str, object] | None = None, input_tables: list[Url] | None = None) -> None: ...
    def __len__(self) -> int: ...
    row_count: Incomplete
    def ensure_data_production_is_ready(self) -> None:
        '''For an _InMemoryRowsTable we produce the table rows in memory

        ## Data production path

          1. If already assembled, return
          2.
              a. If row cache is available, read rows from cache
              b. Else prepare input data and in-memory rows
                1. Prepare "input" data (any setup needed to allow calling input_row and input_len)
                2. Prepare in memory-rows to populate the actual rows
          3. Set the row count
          4. Set the in-memory-rows-valid flag
        '''
