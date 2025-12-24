import pyarrow as pa
from _typeshed import Incomplete
from collections.abc import Mapping, MutableMapping
from tlc.client.bulk_data_url_utils import set_bulk_data_url_prefix as set_bulk_data_url_prefix, set_table_with_bulk_data_url as set_table_with_bulk_data_url
from tlc.client.sample_type import _SampleTypeStructure
from tlc.core.builtins.constants.column_names import DEFAULT_BULK_DATA_SEQUENCE_ID_COLUMN_NAME as DEFAULT_BULK_DATA_SEQUENCE_ID_COLUMN_NAME
from tlc.core.builtins.constants.values import DEFAULT_BULK_DATA_CHUNK_SIZE_MB as DEFAULT_BULK_DATA_CHUNK_SIZE_MB
from tlc.core.builtins.types import MetricData as MetricData, MetricTableInfo as MetricTableInfo
from tlc.core.helpers.bulk_data_helper import BulkDataRowProcessor as BulkDataRowProcessor
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_url import TableFromParquet as TableFromParquet
from tlc.core.project_context import disabled_project_context as disabled_project_context
from tlc.core.schema import Schema as Schema
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from tlc.core.url_adapter import IfExistsOption as IfExistsOption
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.core.utils.string_validation import validate_column_name as validate_column_name
from typing import Any, Literal

logger: Incomplete

class TableWriter:
    '''A class for writing batches of rows to persistent storage.

    This class is primarily used for writing data in a structured format to parquet files. It supports
    batching of data and managing the schema of the columns.

    :Example:

    ```python
    table_writer = TableWriter(
        project_name="My Project",
        dataset_name="My Dataset",
        table_name="My Table"
    )
    table_writer.add_batch({"column1": [1, 2, 3], "column2": ["a", "b", "c"]})
    table_writer.add_row({"column1": 4, "column2": "d"})
    table = table_writer.finalize()
    ```
    '''
    write_option: Incomplete
    description: Incomplete
    buffer: list[pa.RecordBatch]
    max_length: int
    row_count: int
    override_column_schemas: Incomplete
    url: Incomplete
    def __init__(self, table_name: str = ..., dataset_name: str = ..., project_name: str = ..., description: str = '', column_schemas: Mapping[str, _SampleTypeStructure] | Schema | None = None, if_exists: Literal['overwrite', 'rename', 'raise'] = 'rename', root_url: Url | str | None = None, input_tables: list[Url] | None = None, bulk_data_chunk_size_mb: float = ..., bulk_data_context_key: str = ..., bulk_data_url: Url | str | None = None, *, table_url: Url | str | None = None) -> None:
        '''Initialize a TableWriter.

        :param table_name: The name of the table, defaults to "table".
        :param dataset_name: The name of the dataset, defaults to "default-dataset".
        :param project_name: The name of the project, defaults to "default-project".
        :param description: An optional description of the table.
        :param column_schemas: Optional schemas to override the default inferred column schemas. If a Schema is provided
            directly, it must have `values` for the columns.
        :param if_exists: The option to use when the table already exists.
        :param root_url: The root URL to write the table to. If not provided, the default root URL is used.
        :param bulk_data_chunk_size_mb: The size of the chunk in MB for bulk data (default: 50.0 MB).
        :param bulk_data_context_key: The column name to use as the context for bulk data (default: "sequence_id").
        :param table_url: An optional url to manually specify the Url of the written table. Mutually exclusive with
            table_name, dataset_name, and project_name.
        '''
    def __enter__(self) -> TableWriter: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: Any) -> None: ...
    def get_finalized_table(self) -> Table | None:
        """Get the result of the table writing operation.

        Returns None if the context manager exited due to an exception or if the result hasn't been set yet.

        :return: The written table, or None if not available.
        """
    def add_row(self, table_row: MutableMapping[str, MetricData]) -> None:
        """Add a single row to the table being written.

        :param table_row: A dictionary mapping column names to values.
        """
    def add_batch(self, table_batch: MutableMapping[str, MetricData]) -> None:
        """Add a batch of rows to the buffer for writing.

        This method validates the consistency of the batch and appends it to the buffer. When the buffer reaches
        its maximum size, it is automatically flushed to disk.

        :param table_batch: A dictionary mapping column names to lists of values.
        :raises ValueError: If the columns in the batch have unequal lengths or mismatch with existing columns.
        """
    def clear(self) -> None:
        """Clear the buffer and reset the internal state."""
    def finalize(self) -> Table:
        """Write all added batches to disk and return the written table."""
