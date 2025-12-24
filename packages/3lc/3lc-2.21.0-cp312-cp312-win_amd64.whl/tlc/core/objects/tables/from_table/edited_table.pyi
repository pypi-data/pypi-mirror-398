import pyarrow as pa
from _typeshed import Incomplete
from collections.abc import Mapping, Sequence
from tlc.core.builtins.constants.column_names import SHOULD_DELETE as SHOULD_DELETE
from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import DictValue as DictValue, Schema as Schema, StringValue as StringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class EditedTable(_InMemoryColumnsTable):
    '''An editable table that allows sparse modifications to both data and schema.

    :param url: The URL where the table should be persisted.
    :param created: The creation timestamp for the table.
    :param dataset_name: The name of the dataset the table belongs to.
    :param project_name: The name of the project the table belongs to.
    :param row_cache_url: The URL for caching rows.
    :param row_cache_populated: Flag indicating if the row cache is populated.
    :param override_table_rows_schema: Schema overrides for table rows. See also Table.override_table_rows_schema.
    :param init_parameters: Parameters for initializing the table from JSON.
    :param input_table_url: The URL or table reference to be edited.
    :param edits: A dict containing the edits, of the form `{"column_name": {"runs_and_values": [[run1, run2, ...],
        value]}}`.


    ## Edit Operations
    The `edits` dict allows for sparse editing of the table\'s data. Column names act as keys mapping to a struct with a
    `runs_and_values` list. Each pair of elements in this list define a single edit operation.
    An example that changes three rows of the label column to the value "Dog":
    ```python
    edits = {
        "label": {"runs_and_values": [[11, 12, 13], "Dog"]}
    }
    ```
    **Examples of Data Edits:**
    - Change a single value: `{\'label\': {\'runs_and_values\': [[3], 1]}}`
    - Change multiple rows: `{\'label\': {\'runs_and_values\': [[3, 5, 6, 8], 1]}}`
    - Change with multiple edits: `{\'label\': {\'runs_and_values\': [[3, 5], 1, [6,7], 2]}}`
    - Edit a contiguous range: `{\'modified\': {\'runs_and_values\': [[1, -5], True]}}`
      - Using a negative index indicates a range. The range is inclusive of the start index and the end index. I.e.
        [1,-5] === [1,2,3,4,5].

    ## Schema Edits
    You can alter the table\'s schema through the `override_table_rows_schema` property. Schema edits can be nested and
    may also be specified in a sparse format *but no sparser than ScalarValue granularity*.

    Some examples:

    - Adding a new column to a table
      ```python
      override_schema = {"values": {"new_column": {"value": {"type": "int32"}}}}
      table_with_new_column = EditedTable(input_table_url=table,
                                          override_table_rows_schema=override_schema)
      ```
    - Adding a New Category to a Column in a Table.

    Given a Cat or Dog value map the user may want to include an additional category (Frog). In this case the complete
    value map must be specified since its a sub component of the column\'s ScalarValue.
      ```python
      override_schema = {"values": {"label": {"value": {
        "type": "int32",
        "map": {
          "0": {"internal_name": "Cat"},
          "1": {"internal_name": "Dog"},
          "2": {"internal_name": "Frog"}
      }}}}}
      table_with_new_category = EditedTable(input_table_url=table,
                                            override_table_rows_schema=override_schema)
      ```
    - Deleting a Column from a Table is done by setting the override to null:
      ```python
      override_schema = {"values": {"My_Int": null}}
      table_without_my_int = EditedTable(input_table_url=table,
                                         override_table_rows_schema=override_schema)
      ```

    - Deleting a Row from a Table is done by editing the value of the special column `SHOULD_DELETE` to `True`:
      ```python
      edits = {
          "SHOULD_DELETE": {"runs_and_values": [[3], True]}
      }
      table_without_row_3 = EditedTable(input_table_url=table, edits=edits)
      ```

    ## A Note on the Size of Edits
    Edits are expected to be small and are ideal for human-interactive input. For large edits, consider using
    external data sources like Parquet files or other procedural tables.
    '''
    edits: Incomplete
    input_table_url: ObjectReference
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_table_url: Url | Table | None = None, edits: Mapping[str, object] | None = None, input_tables: list[Url] | None = None) -> None:
        """Creates a EditedTable from a input Table and a struct of edits.

        :param input_table_url: Url to the input table.
        :param edits: Struct representing the edits to apply to the input table.
        :param url: Optional Url where the EditedTable can later be accessed.
        """
    @staticmethod
    def indices_to_run(indices: Sequence[int]) -> list[int]:
        """Convert a list of indices to a run-length encoded list.

        The output is a single list where negative numbers indicate the end of a consecutive range.

        Example:
            [1, 3, 4, 5, 7, 8] -> [1, 3, -5, 7, -8]
            Where [3, -5] represents the consecutive range [3, 4, 5]

        :param indices: List of indices to convert to runs
        :returns: A run-length encoded list where negative numbers indicate range ends
        """
    def get_input_table(self) -> pa.Table: ...
