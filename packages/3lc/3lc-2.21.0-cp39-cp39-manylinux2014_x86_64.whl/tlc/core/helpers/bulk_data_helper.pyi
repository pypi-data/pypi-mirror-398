import numpy as np
from _typeshed import Incomplete
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Float32Value as Float32Value, Float64Value as Float64Value, Int16Value as Int16Value, Int32Value as Int32Value, Int64Value as Int64Value, Int8Value as Int8Value, NumericValue as NumericValue, Schema as Schema, Uint64Value as Uint64Value
from tlc.core.url import Url as Url
from typing import Any

CODEBOOK_URL_SEPARATOR: str
CODEBOOK_PROPERTY_SUFFIX: str
CODEBOOKRAW_FILE_EXTENSION: str
CODEBOOKRAW_START_AND_LENGTH_SEPARATOR: str
CODEBOOKRAW_STRING_ROLE: str
DEFAULT_CHUNK_SIZE_MB: float

class BulkDataHelper:
    """Helper class for working with bulk data."""
    @staticmethod
    def get_bulk_data_property_url(property_name: str) -> str:
        """Get the bulk data property URL for a given property name.
        :param property_name: The name of the property to get the bulk data property URL for.
        :return: The bulk data property URL.

        :example:
        ```Python
        BulkDataHelper.get_bulk_data_property_url('vertices_3d')
        # 'vertices_3d_binary_property_url'

        BulkDataHelper.get_bulk_data_property_url('sensors_2d.instances.vertices_2d_additional_data.range')
        # 'sensors_2d.instances.vertices_2d_additional_data.range_binary_property_url'
        ```
        """
    @staticmethod
    def get_bulk_data_url(base_path: Url, start: int, length: int) -> str:
        """Get the bulk data URL for a given base path, start, and length.
        :param base_path: The base path to the bulk data file. (can be absolute or relative)
        :param start: The start offset of the data in the file.
        :param length: The length of the data in the file.
        :return: The bulk data URL.
        """

class BinaryChunkWriter:
    """Writes numpy arrays to a binary chunk file and tracks offsets.

    This class manages writing of raw binary data to a file, tracking the current
    position for offset-based URL generation. It will be used as an intermediate
    format that can later be virtualized.

    :param file_path: Path to the binary chunk file to write
    :param table_url: URL of the parent table for relative path calculation
    :param max_size_bytes: Maximum size in bytes before rotation is suggested
    """
    file_path: Incomplete
    table_url: Incomplete
    max_size_bytes: Incomplete
    current_position: int
    def __init__(self, file_path: Path, table_url: Url, max_size_bytes: float) -> None: ...
    def write_array(self, array: np.ndarray) -> str:
        """Write a numpy array to the chunk file and return a URL reference.

        The array is flattened and written as raw bytes. Returns a URL string
        in the format: 'relative/path/file.raw:offset-length'

        :param array: Numpy array to write
        :return: URL string with offset and length
        """
    def should_rotate(self) -> bool:
        """Check if the chunk file has reached its size limit.

        :return: True if the current position exceeds the max size
        """
    def close(self) -> None:
        """Close the file handle if open."""

class BulkDataRowProcessor:
    """Processes rows to extract bulk data arrays and replace with URL references.

    This class uses a unified configuration that can span multiple columns.
    All configured leaf arrays are written into a shared chunk per context (e.g., per sequence),
    which tends to be more efficient when writing row-by-row.

    :param table_url: The URL of the target table (used to compute relative URLs)
    :param paths: Sequence of full leaf paths to store as bulk data. All paths share
        one chunk file per context in ``<table_url>/../../bulk_data``.
    :param context_key: Optional row key used to group chunks (e.g., ``sequence_id``)
    :param chunk_size_mb: Maximum chunk file size in megabytes
    """
    table_url: Incomplete
    bulk_data_dir_url: Incomplete
    chunk_size_bytes: Incomplete
    paths: list[str]
    context_key: Incomplete
    chunk_writers: dict[str, BinaryChunkWriter]
    chunk_counters: dict[str, int]
    def __init__(self, table_url: Url, paths: Sequence[str] | None = None, context_key: str | None = None, chunk_size_mb: float = ..., bulk_data_url: Url | Path | str | None = None) -> None: ...
    def process_row(self, row: dict[str, Any]) -> dict[str, Any]:
        """Process a row to extract arrays and replace with URL references.

        For each configured full path:
          - Traverses the row structure (lists are handled automatically)
          - Writes found arrays to the shared chunk file for the row's context
          - Replaces the leaf with a sibling ``<leaf>_binary_property_url`` string or list of strings

        :param row: Input row dictionary with actual numpy arrays
        :return: Modified row with arrays replaced by URL references
        """
    def process_batch(self, batch: MutableMapping[str, list[Any]]) -> MutableMapping[str, list[Any]]: ...
    def close_all(self) -> None:
        """Close all active chunk writers."""

class BulkDataAccessor:
    """Helper class for accessing bulk data rows from a Table."""
    def __init__(self, table: Table) -> None:
        """Initialize the BulkDataAccessor.

        :param table: The Table to access bulk data rows from.
        """
    def __getitem__(self, idx: int) -> Mapping[str, object]:
        """Access a row and materialize bulk-data URL fields into numpy arrays."""
    def __len__(self) -> int: ...
