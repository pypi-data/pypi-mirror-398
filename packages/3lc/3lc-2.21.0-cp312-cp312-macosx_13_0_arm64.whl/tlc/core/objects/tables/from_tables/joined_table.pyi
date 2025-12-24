from collections.abc import Sequence
from tlc.core.builtins.constants.string_roles import STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.objects.tables.from_url import TableFromParquet as TableFromParquet
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Schema as Schema, StringValue as StringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

class JoinedTable(_InMemoryColumnsTable):
    '''
    A procedural table where multiple input tables are joined into a singular table.

    This table allows for combining tables in a procedural fashion and provides tools
    to manage the collective data and schemas of these joined tables.

    :Example:

    ```Python
    from tlc.core.objects.tables import JoinedTable
    from tlc.core.url import Url

    first_table = ...
    second_table = ...

    joined_table_url = Url("/path/to/joined_table.json")
    joined_table = JoinedTable(url=joined_table_url, input_table_urls=[first_table, second_table])
    assert len(joined_table) == len(first_table) + len(second_table)
    # A joined table has now been created, but it is not yet persisted.

    joined_table.write_to_url()
    # The joined table is now persisted to the given URL.
    ```

    The tables being joined must have the same columns, but the columns are allowed to have different schemas.
    In this case, the schemas will be joined together, with the following rules:

    - If the schemas are atomic (i.e. they have a value), the schemas must be compatible (i.e. have the same type).
        If the values have different value maps, a new joined value map will be created.
    - If the schemas are not atomic (i.e. they have sub-schemas), the schemas will be joined recursively.
    - If any of the schemas are incompatible, a ValueError will be raised.
    '''
    input_table_urls: list[ObjectReference]
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, input_table_urls: Sequence[Url | Table] | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None:
        """Create a new JoinedTable object.

        :param url: The URL where the table should be persisted.
        :param created: The creation timestamp for the table.
        :param dataset_name: The name of the dataset the table belongs to.
        :param row_cache_url: The URL for caching rows.
        :param row_cache_populated: Flag indicating if the row cache is populated.
        :param input_table_urls: A list of URLs or table references for the tables to be joined.
        :param init_parameters: Parameters for initializing the table from JSON.
        """
    def flatten_input_files(self) -> list[Url]:
        """Collect the `input_url` property of all TableFromParquet leaf-tables"""
