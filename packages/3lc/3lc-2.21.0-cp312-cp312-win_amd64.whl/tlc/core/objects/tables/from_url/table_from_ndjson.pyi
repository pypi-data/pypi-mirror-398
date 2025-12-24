from _typeshed import Incomplete
from tlc.client.sample_type import SampleType as SampleType
from tlc.core.builtins.constants.string_roles import STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

logger: Incomplete

class TableFromNdjson(_InMemoryColumnsTable):
    """A table populated from a NDJSON file at a given URL."""
    input_url: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_tables: list[Url] | None = None, input_url: Url | str | None = None) -> None:
        """Initialize a TableFromNdjson object.

        :param url: The URL of the table.
        :param created: The creation date of the table.
        :param description: The description of the table.
        :param row_cache_url: The URL of the row cache.
        :param row_cache_populated: Whether the row cache is populated.
        :param override_table_rows_schema: The table rows schema to override.
        :param init_parameters: The parameters used to initialize the table.
        :param input_tables: A list of Table Urls that should be used as input tables.
        :param input_url: The URL of the input data.
        """
