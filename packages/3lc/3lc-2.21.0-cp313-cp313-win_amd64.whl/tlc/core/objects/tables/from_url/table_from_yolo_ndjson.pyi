from _typeshed import Incomplete
from tlc.client.sample_type import CategoricalLabel as CategoricalLabel
from tlc.core.builtins.constants.column_names import HEIGHT as HEIGHT, IMAGE as IMAGE, LABEL as LABEL, WIDTH as WIDTH
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import TableRow as TableRow
from tlc.core.objects.tables.from_url.table_from_ndjson import TableFromNdjson as TableFromNdjson
from tlc.core.schema import ImageUrlStringValue as ImageUrlStringValue, Schema as Schema
from tlc.core.url import Url as Url
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any

logger: Incomplete

class _ClassificationMixin: ...

class TableFromYoloNdjson(TableFromNdjson):
    """A table populated from a NDJSON file at a given URL."""
    split: Incomplete
    image_folder_url: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_tables: list[Url] | None = None, input_url: Url | str | None = None, image_folder_url: Url | str | None = None, split: str | None = None) -> None:
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
        :param image_folder_url: The folder containing the images, used to handle relative paths.
        :param split: The split of the input data to get. Rows with a different 'split' are ignored.
        """
