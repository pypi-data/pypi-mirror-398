import pandas as pd
import pyarrow as pa
from _typeshed import Incomplete
from collections.abc import Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import cached_property as cached_property
from pathlib import Path
from tlc.client.sample_type import CategoricalLabel as CategoricalLabel, PILImage as PILImage, SampleType as SampleType, _SampleTypeStructure
from tlc.client.utils import RangeSampler as RangeSampler, RepeatByWeightSampler as RepeatByWeightSampler, SubsetSequentialSampler as SubsetSequentialSampler, standardized_transforms as standardized_transforms
from tlc.core.builtins.constants.column_names import FOREIGN_TABLE_ID as FOREIGN_TABLE_ID, SAMPLE_WEIGHT as SAMPLE_WEIGHT, SHOULD_DELETE as SHOULD_DELETE
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_SAMPLE_WEIGHT as NUMBER_ROLE_SAMPLE_WEIGHT, NUMBER_ROLE_TABLE_ROW_INDEX as NUMBER_ROLE_TABLE_ROW_INDEX
from tlc.core.builtins.constants.string_roles import STRING_ROLE_DATETIME as STRING_ROLE_DATETIME, STRING_ROLE_TABLE_URL as STRING_ROLE_TABLE_URL
from tlc.core.builtins.schemas.row_count_schema import row_count_schema as row_count_schema
from tlc.core.export import Exporter as Exporter, infer_format as infer_format
from tlc.core.object import Object as Object
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.tables.from_python_object.table_from_pandas import TableFromPandas as TableFromPandas
from tlc.core.objects.tables.from_python_object.table_from_pydict import TableFromPydict as TableFromPydict
from tlc.core.objects.tables.from_python_object.table_from_torch_dataset import TableFromTorchDataset as TableFromTorchDataset
from tlc.core.objects.tables.from_url.table_from_coco import TableFromCoco as TableFromCoco
from tlc.core.objects.tables.from_url.table_from_csv import TableFromCsv as TableFromCsv
from tlc.core.objects.tables.from_url.table_from_ndjson import TableFromNdjson as TableFromNdjson
from tlc.core.objects.tables.from_url.table_from_parquet import TableFromParquet as TableFromParquet
from tlc.core.objects.tables.from_url.table_from_yolo import TableFromYolo as TableFromYolo
from tlc.core.objects.tables.from_url.table_from_yolo_ndjson import TableFromYoloNdjson as TableFromYoloNdjson
from tlc.core.project_context import ProjectContext as ProjectContext
from tlc.core.schema import BoolValue as BoolValue, DictValue as DictValue, DimensionNumericValue as DimensionNumericValue, MapElement as MapElement, NumericValue as NumericValue, ScalarValue as ScalarValue, Schema as Schema, SegmentationUrlStringValue as SegmentationUrlStringValue, StringValue as StringValue, UrlStringValue as UrlStringValue, ValueMapLike as ValueMapLike
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.table_row_serializer_registry import TableRowSerializerRegistry as TableRowSerializerRegistry
from tlc.core.url import Scheme as Scheme, Url as Url, UrlAliasRegistry as UrlAliasRegistry
from tlc.core.url_adapter import IfExistsOption as IfExistsOption
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.integration.hugging_face import TableFromHuggingFace as TableFromHuggingFace
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from torch.utils.data import Dataset as TorchDataset
from torch.utils.data.sampler import Sampler as Sampler
from typing import Any, Callable, Literal

logger: Incomplete
TableRow = Mapping[str, object]

class ImmutableDict(dict[str, object]):
    """An immutable access interface to a nested dictionary representing a TableRow.

    This class is used to make access to table rows immutable, and to provide a consistent interface for accessing
    nested column data.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __readonly__(self, *args: Any, **kwargs: Any) -> None: ...
    __setitem__ = __readonly__
    __delitem__ = __readonly__
    clear = __readonly__
    pop = __readonly__
    popitem = __readonly__
    setdefault = __readonly__
    update = __readonly__
    def copy(self) -> dict[str, object]:
        """Return a deep copy of the dict as a standard mutable dict."""
    def __reduce__(self) -> Any: ...

class TableRows:
    """An immutable access interface to the rows of a Table object"""
    def __init__(self, table: Table) -> None: ...
    def __getitem__(self, row: int) -> TableRow:
        """Get the item at the given row in the table"""
    def __iter__(self) -> Iterator[TableRow]: ...

class Table(Object):
    '''The abstract base class for all Table types.

    :::{warning}
    Do not instantiate this class directly. Use one of the `Table.from_*` methods instead.
    :::

    A Table is an object with two specific responsibilities:

    1) Creating table rows on demand (Either through the row-based access interface {func}`table_rows<table_rows>`,
    or through the sample-based access interface provided by `__getitem__`).

    2) Creating a schema which describes the type of produced rows
    (through the {func}`rows_schema<rows_schema>` property)

    Both types of produced data are determined by immutable properties defined by each particular Table type.

    **ALTERNATIVE INTERFACE/CACHING:**

    A full representation of all table rows can - for performance reasons - also be retrieved through the
    {func}`get_rows_as_binary<get_rows_as_binary>` method.

    This method will try to retrieve a cached version of the table rows if

    - `row_cache_url` is non-empty AND
    - `row_cache_populated` is `True`

    When this is the case, it is guaranteed that the `schema` property of the table is fully populated,
    including the nested \'rows_schema\' property which defines the layout of all table rows.

    When this cached version is NOT defined, however, get_rows_as_binary() needs to iterate over all rows to produce the
    data.

    If `row_cache_url` is non-empty, the produced binary data will be cached to the specified location. After successful
    caching, the updated Table object will be written to its backing URL *exactly once*, now with \'row_cache_populated\'
    set to True and with the schema fully updated. Also, the `row_count` property is guaranteed to be correct at this
    time.

    Whether accessing data from a Table object later refers to this cached version (or produces the data itself)
    is implementation specific.

    **STATE MUTABILITY:**

    As described above, Tables are constrained in how they are allowed to change state:

    - The data production parameters ("recipe") of a table are immutable
    - The persisted JSON representation of a Table (e.g. on disk) can take on three different states, and each state can
      be written only once:

      1) Bare-bones recipe
      2) Bare-bones recipe + full schema + \'row_count\' (\'row_cache_populated\' = False)
      3) Bare-bones recipe + full schema + \'row_count\' (\'row_cache_populated\' = True)
    '''
    project_name: str | None
    dataset_name: str | None
    description: str
    row_cache_url: Incomplete
    row_cache_populated: bool
    override_table_rows_schema: Schema
    row_count: int
    rows: list
    input_tables: list[Url]
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None:
        """
        :param url: The URL of the table.
        :param created: The creation time of the table.
        :param description: The description of the table.
        :param row_cache_url: The URL of the row cache.
        :param row_cache_populated: Whether the row cache is populated.
        :param override_table_rows_schema: The schema to override the table rows schema.
        :param init_parameters: The initial parameters of the table.
        :param input_tables: A list of Table URLs that are considered direct predecessors in this table's lineage. This
            parameter serves as an explicit mechanism for tracking table relationships beyond the automatic lineage
            tracing typically managed by subclasses.
        """
    def __iter__(self) -> Iterator[object]: ...
    def ensure_complete_schema(self) -> None:
        """Ensure that the table has a complete schema."""
    def copy(self, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'rename', 'overwrite'] = 'raise', *, destination_url: Url | None = None) -> Table:
        """Create a copy of this table.

        The copy is performed to:
          1. A URL derived from the given table_name, dataset_name, project_name, and root_url if given
          2. destination_url, if given
          3. A generated URL derived from the tables's URL, if none of the above are given

        :param table_name: The name of the table to copy to.
        :param dataset_name: The name of the dataset to copy to.
        :param project_name: The name of the project to copy to.
        :param root_url: The root URL to copy to.
        :param if_exists: The behavior to use if the destination URL already exists.
        :param destination_url: The URL to copy the table to.
        :returns: The copied table.
        """
    def ensure_dependent_properties(self) -> None:
        """Ensure that the table set row_count as required to reach fully defined state."""
    def ensure_data_production_is_ready(self) -> None:
        """A method that ensures that the table is ready to produce data

        This method is called before any access to the Table's data is made. It is used to ensure that the Table has
        preformed any necessary data production steps. Normally Tables don't produce data until it is requested, but
        this method can be called to force data production.

        Note that subsequent applications of this method will not change the data, as a Table is immutable.
        """
    def __len__(self) -> int:
        """Compute the number of rows in this table, this can be a costly operation"""
    def __getitem__(self, index: int) -> object: ...
    @property
    def collecting_metrics(self) -> bool:
        """Getter for collecting_metrics."""
    @collecting_metrics.setter
    def collecting_metrics(self, value: bool) -> None:
        """Setter for collecting_metrics, which restricts direct modification."""
    @contextmanager
    def collection_mode(self) -> Iterator[None]:
        """Enable metrics-collection mode on the Table.

        When collecting metrics mode is enabled, only maps defined by calls to `map_collect_metrics()` are applied to
        the table rows.
        """
    @property
    def row_schema(self) -> Schema:
        """Returns the schema for a single row of this table."""
    @property
    def rows_schema(self) -> Schema:
        """Returns the schema for all rows of this table."""
    @cached_property
    def table_rows(self) -> TableRows:
        """Access the rows of this table as an immutable mapping."""
    @property
    def name(self) -> str:
        """The name of the table."""
    def get_row_cache_size(self) -> int:
        """Returns the size of the row cache in bytes."""
    def set_row_cache_url(self, row_cache_url: Url | str) -> bool:
        """Assign a new row_cache_url value.

        Will set row_cache_populated to False if the cache file has changed.

        :param row_cache_url: The new row_cache_url value.
        :returns: True if the row_cache_url value was changed, False otherwise.
        """
    @staticmethod
    def transform_value(schema: Schema | None, item: object) -> object:
        """Transform a single table value according to the schema.

        3LC currently only uses pure string representations of datetime values. This helper function is used to convert
        any timestamps to strings.

        :param schema: The schema corresponding to the column of the value.
        :param item: The value to transform.
        """
    def is_all_parquet(self) -> bool:
        """
        Return True if the backing data for this table is all parquet files.
        """
    def write_to_row_cache(self, create_url_if_empty: bool = False, overwrite_if_exists: bool = True) -> None:
        """Cache the table rows to the row cache Url.

        If the table is already cached, or the Url of the Table is an API-Url, this method does nothing.

        In the case where self.row_cache_url is empty, a new Url will be created and assigned to self.row_cache_url
        if create_url_if_empty is True, otherwise a ValueError will be raised.

        :param create_url_if_empty: Whether to create a new row cache Url if self.row_cache_url is empty.
        :param overwrite_if_exists: Whether to overwrite the row cache file if it already exists.
        """
    def get_rows_as_binary(self, exclude_bulk_data: bool = False) -> bytes:
        """Return all rows of the table as a binary Parquet buffer, with optional exclusion of bulk data columns.

        This method will return the 'Table-representation' of the table, which is the most efficient representation,
        since only references to the input data are stored.

        :param exclude_bulk_data: Whether to exclude bulk data columns from the serialized rows.
        :returns: The rows of the table as a binary Parquet buffer.
        """
    def should_include_schema_in_json(self, schema: Schema) -> bool:
        """Only include the schema in the JSON representation if it is not empty."""
    def latest(self, use_new_columns: bool = True, wait_for_rescan: bool = True, timeout: float | None = None) -> Table:
        """Return the most recent version of the table, as indexed by the TableIndexingTable indexing mechanism.

        This function retrieves the latest version of this table that has been indexed or exists in the ObjectRegistry.
        If desired it is possible to wait for the next indexing run to complete by setting wait_for_rescan to True
        together with a timeout in seconds.

        For more information about how the indexing system works, see the [indexing](python-package-indexing) page.

        :Example:

        ```python
        table_instance = Table()
        ... # working
        latest_table = table_instance.latest()
        ```
        :param use_new_columns: If new columns have been added to the latest revision of the Table, whether to include
        these values in the sample-view of the Table. Defaults to True.
        :param rescan: Whether to rescan the TableIndexingTable (lineage) before trying to resolve latest revision.
                       Defaults to True.
        :param timeout: The timeout in seconds to block when waiting for the next indexing run to complete. Defaults to
                          None meaning that indexing can run forever.
        :returns: The latest version of the table.

        :raises ValueError: If the latest version of the table cannot be found in the dataset or if an error occurs when
                            attempting to create an object from the latest Url.
        """
    def revision(self, tag: Literal['latest'] | None = None, table_url: Url | str = '', table_name: str = '') -> Table:
        """Return a specific revision of the table.

        This function retrieves a specific revision of this table. The revision can be specified by tag, table_url, or
        table_name. If no arguments are provided, the current table is returned.

        :param tag: The tag of the revision to return. Currently only 'latest' is supported.
        :param table_url: The URL of the revision to return.
        :param table_name: The name of the revision to return.
        """
    def squash(self, output_url: Url | str | None = None, dataset_name: str | None = None, project_name: str | None = None, table_name: str | None = None, root: Url | str | None = None, input_tables: list[Table | Url | str] | None = None) -> Table:
        """Create a copy of this table where all lineage is squashed.

        A squashed table is a table where all lineage is merged. This is useful for creating a table that is
        independent of its parent tables. This function creates a new table with the same rows as the original table,
        but with no lineage. The new table is written to the `output_url`, or placed in the same project and dataset as
        this table if no output URL is provided.

        :param output_url: The output url for the squashed table. Mutually exclusive with table_name, dataset_name and
                           project_name.
        :param dataset_name: The dataset name to use for the squashed table. If not provided, the dataset_name of the
                             original table is used.
        :param project_name: The project name to use for the squashed table. If not provided, the project_name of the
                             original table is used.
        :param table_name: The name of the squashed table. If not provided, a uniquified variant of 'squashed' is used.
        :param input_tables: Optional list of Tables or URLs to Tables to refer to as the input tables for the squashed
                             table. By default, no tables are referred to as inputs.

        :returns: The squashed table.
        """
    @property
    def pyarrow_schema(self) -> pa.Schema | None:
        """
        Returns a pyarrow schema for this table
        """
    @property
    def columns(self) -> list[str]:
        """Return a list of column names for this table."""
    @property
    def bulk_data_url(self) -> Url:
        """Return the sample url for this table.

        The bulk data url is the url to the folder containing any bulk data for this table.
        """
    def to_pandas(self) -> pd.DataFrame:
        """
        Return a pandas DataFrame for this table.

        :returns: A pandas DataFrame populated from the rows of this table.
        """
    def get_column(self, name: str, combine_chunks: bool = True) -> pa.Array | pa.ChunkedArray:
        """
        Return a the specified column of the table as a pyarrow table.

        To get nested sub-columns, use dot notation. E.g. 'column.sub_column'. The values in the column will be
        the row-view of the table. A column which is a PIL image in its sample-view, for instance, will be returned as
        a column of strings.

        :param name: The name of the column to get.
        :param combine_chunks: Whether to combine the chunks of the returned column in the case that it is a
            ChunkedArray. Defaults to True.
        :returns: A pyarrow table containing the specified column.
        :raises KeyError: If the column does not exist in the table.
        """
    def add_column(self, column_name: str, values: list[object] | object, schema: Schema | None = None, url: Url | None = None) -> Table:
        """Create a derived table with a column added.

        This method creates and returns a new revision of the table with a new column added.

        :param column_name: The name of the column to add.
        :param values: The values to add to the column. This can be a list of values, or a single value to be added to
                          all rows.
        :param schema: The schema of the column to add. If not provided, the schema will be inferred from the values.
        :param url: The url to write the new table to. If not provided, the new table will be located next to the
                    current table.

        :returns: A new table with the column added.
        """
    def delete_column(self, column_name: str, *, table_name: str | None = None, table_url: Url | str = '', description: str | None = None) -> Table:
        """Create a derived table with a column deleted.

        This method creates and returns a new revision of the table with a column deleted.

        :param column_name: The name of the column to delete.
        :param table_name: The name of the new table. If not provided and table_url is not provided, a default name will
            be used.
        :param table_url: The url to write the new table to. If not provided, the new table will be located next to the
                    current table.
        :param description: A description of the table. If not provided, a default description will be used.

        :returns: A new table with the column deleted.
        """
    def delete_columns(self, column_names: Sequence[str], *, table_name: str | None = None, table_url: Url | str = '', description: str | None = None) -> Table:
        """Create a derived table with columns deleted.

        This method creates and returns a new revision of the table with the specified columns deleted.

        :param column_names: The names of the columns to delete.
        :param table_name: The name of the new table. If not provided and table_url is not provided, a default name will
            be used.
        :param table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :param description: A description of the table. If not provided, a default description will be used.

        :returns: A new table with the columns deleted.
        """
    def delete_rows(self, indices: Sequence[int], *, table_name: str | None = None, table_url: Url | str = '', description: str | None = None) -> Table:
        """Delete rows from a Table.

        This method creates and returns a new revision of the table with the specified rows deleted.

        :param indices: The indices of the rows to delete.
        :param table_name: The name of the new table. If not provided and table_url is not provided, a default name will
            be used.
        :param table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :param description: A description of the table. If not provided, a default description will be used.

        :returns: A new table with the rows deleted.
        """
    def delete_row(self, index: int, *, table_name: str | None = None, table_url: Url | str = '', description: str | None = None) -> Table:
        """Delete a row from a Table.

        This method creates and returns a new revision of the table with the specified row deleted.

        :param index: The index of the row to delete.
        :param table_name: The name of the new table. If not provided and table_url is not provided, a default name will
            be used.
        :param table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :param description: A description of the table. If not provided, a default description will be used.

        :returns: A new table with the row deleted.
        """
    def set_value_map(self, value_path: str, value_map: dict[float, Any], *, edited_table_url: Url | str = '') -> Table:
        """Set a value map for a specified numeric value within the schema of the Table.

        Sets a value map for a value within the schema of the Table, returning a new table revision
        with the applied value map.

        This method creates and returns a new revision of the table with a overridden value map for a specific numeric
        value.

        Any item in a {class}`Schema<tlc.core.schema.Schema>` of type
        {class}`NumericValue<tlc.core.schema.NumericValue>` can have a value map. A value map is a mapping from a
        numeric value to a {class}`MapElement<tlc.core.schema.MapElement>`, where a
        {class}`MapElement<tlc.core.schema.MapElement>` contains metadata about a categorical value such as category
        names and IDs.

        :::{admonition} Partial Value Maps
        Value maps may be partial, i.e. they may only contain a mapping for a subset of the possible
        numeric values. Indeed they can be floating point values, which can be useful for annotating continuous
        variables with categorical metadata, such as color or label.
        :::

        For more fine-grained control over value map editing, see
        {func}`Table.set_value_map_item<tlc.core.objects.table.Table.set_value_map_item>` and
        {func}`Table.add_value_map_item<tlc.core.objects.table.Table.add_value_map_item>`, and
        {func}`Table.delete_value_map_item<tlc.core.objects.table.Table.delete_value_map_item>`.

        :param value_path: The path to the value to add the value map to. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :param value_map: The value map to set on the value. The value will be converted to a a dictionary mapping from
            floating point values to {class}`MapElement<tlc.core.schema.MapElement>` if it is not already.
        :param edited_table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :returns: A new table with the value map set.
        :raises ValueError: If the value path does not exist or is not a
            {class}`NumericValue<tlc.core.schema.NumericValue>`.
        """
    def delete_value_map(self, value_path: str, *, edited_table_url: Url | str = '') -> Table:
        """Delete a value map for a specified numeric value within the schema of the Table.

        This method creates and returns a new revision of the Table with a deleted value map for a specific numeric
        value.

        :param value_path: The path to the value to add the value map to. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :param edited_table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :returns: A new table with the value map deleted.
        :raises ValueError: If the value path does not exist or is not a
            {class}`NumericValue<tlc.core.schema.NumericValue>`.
        """
    def set_value_map_item(self, value_path: str, value: float | int, internal_name: str, display_name: str = '', description: str = '', display_color: str = '', url: Url | str = '', *, edited_table_url: Url | str = '') -> Table:
        '''Update an existing value map item for a specified numeric value within the schema of the Table.

        This method creates and returns a new revision of the table with a value map item added to a value in a column.

        :Example:
        ```python
        table = Table.from_url("cats-and-dogs")
        new_table = table.set_value_map_item("label", 0, "cat")
        # new_table is now a new revision of the table with a updated value map item added to the value 0 in the column
        assert table.latest() == new_table, "The new table is the latest revision of the table."
        ```

        To add a new value map item at the next available value in the value map, see
        {func}`Table.add_value_map_item<tlc.core.objects.table.Table.add_value_map_item>`.

        To delete a value map item, see
        {func}`Table.delete_value_map_item<tlc.core.objects.table.Table.delete_value_map_item>`.

        :param value_path: The path to the value to add the value map item to. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :param value: The numeric value to add the value map item to. If the value already exists, the value map item
            will be updated.
        :param internal_name: The internal name of the value map item. This is the primary identifier of the value map
            item.
        :param display_name: The display name of the value map item.
        :param description: The description of the value map item.
        :param display_color: The display color of the value map item.
        :param url: The url of the value map item.
        :param edited_table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :raises ValueError: If the value path does not exist or is not a
            {class}`NumericValue<tlc.core.schema.NumericValue>`.
        '''
    def add_value_map_item(self, value_path: str, internal_name: str, display_name: str = '', description: str = '', display_color: str = '', url: Url | str = '', *, value: float | int | None = None, edited_table_url: Url | str = '') -> Table:
        """Add a value map item for a specified numeric value within the schema of the Table.

        Adds a new value map item to the schema of the Table without overwriting existing items.

        If the specified value or internal name already exists in the value map, this method will raise an error to
        prevent overwriting.

        For more details on value maps, refer to the documentation for
        {func}`Table.set_value_map<tlc.core.objects.table.Table.set_value_map>`.

        :param value_path: The path to the value to add the value map item to. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :param internal_name: The internal name of the value map item. This is the primary identifier of the value map
            item.
        :param display_name: The display name of the value map item.
        :param description: The description of the value map item.
        :param display_color: The display color of the value map item.
        :param url: The url of the value map item.
        :param value: The numeric value to add the value map item to. If not provided, the value will be the next
            available value in the value map (starting from 0).
        :param edited_table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :returns: A new table with the value map item added.
        :raises ValueError: If the value path does not exist or is not a
            {class}`NumericValue<tlc.core.schema.NumericValue>`, or if the value or internal name already exists in the
            value map.
        """
    def delete_value_map_item(self, value_path: str, *, value: float | int | None = None, internal_name: str = '', edited_table_url: Url | str = '') -> Table:
        """Delete a value map item for a specified numeric value within the schema of the Table.

        Deletes a value map item from the schema of the Table, by numeric value or internal name.

        For more details on value maps, refer to the documentation for
        {func}`Table.set_value_map<tlc.core.objects.table.Table.set_value_map>`.

        :param value_path: The path to the value to add the value map item to. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :param value: The numeric value of the value map item to delete. If not provided, the value map item will be
            deleted by internal name.
        :param internal_name: The internal name of the value map item to delete. If not provided, the value map item
            will be deleted by numeric value.
        :param edited_table_url: The url of the edited table. If not provided, the new table will be located next to the
            current table.
        :returns: A new table with the value map item deleted.
        :raises ValueError: If the value path does not exist or is not a
            {class}`NumericValue<tlc.core.schema.NumericValue>`, or if the value or internal name does not exist in the
            value map.
        """
    def get_value_map(self, value_path: str) -> dict[float, MapElement] | None:
        """Get the value map for a value path.

        :param value_path: The path to the value to get the value map for. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :returns: A value map for the value, or None if the value does not exist or does not have a value map.
        """
    def get_simple_value_map(self, value_path: str) -> dict[int, str] | None:
        """Get the simple value map for a value path, mapping class indices to class names.

        :param value_path: The path to the value to get the value map for. Can be the name of a column, or a
            dot-separated path to a sub-value in a composite column.
        :returns: A simple value map for the value, or None if the value does not exist or does not have a value map.
        """
    def export(self, output_url: Url | str | Path, format: str | None = None, weight_threshold: float = 0.0, **kwargs: object) -> None:
        """Export this table to the given output url.

        :param output_url: The output url to export to.
        :param format: The format to export to. If not provided, the format will be inferred from the table and the
            output url.
        :param weight_threshold: The weight threshold to use for exporting. If the table has a weights column, rows
            with a weight below this threshold will be excluded from the export.
        :param kwargs: Additional arguments to pass to the exporter. Which arguments are valid depends on the format.
            See the documentation for the subclasses of Exporter for more information.
        """
    def is_descendant_of(self, other: Table) -> bool:
        """Return True if this table is a descendent of the provided table.

        :param other: The table to check if this table is a descendant of.
        :returns: True if this table is a descendant of the provided table, False otherwise."""
    def get_foreign_table_url(self, column: str = ...) -> Url | None:
        """Return the input table URL referenced by this table.

        This method is intended for tables that reference a single input table. Typically, this would be a metrics table
        of per-example metrics collected using another table.

        If the table contains a column named 'input_table_id' with value map indicating it references a input
        table by Url, this method returns the Url of that input table.

        :param column: The name of the column to check for a foreign key.
        :returns: The URL of the foreign table, or None if no input table is found.
        """
    @property
    def weights_column_name(self) -> str | None:
        """Return the name of the column containing the weights for this table, or None if no such column exists."""
    def create_sampler(self, exclude_zero_weights: bool = True, weighted: bool = True, shuffle: bool = True, repeat_by_weight: bool = False) -> Sampler[int]:
        """Returns a sampler based on the weights column of the table. The type and behavior of the returned Sampler
        also depends on the values of the argument flags.

        :param exclude_zero_weight: If True, rows with a weight of zero will be excluded from the sampler. This is
            useful for reducing the length of the sampler for datasets with zero-weighted samples, and thus the length
            of an epoch when using a PyTorch DataLoader.
        :param weighted: If True, the sampler will use sample weights (beyond the exclusion of zero-weighted rows) to
            ensure that the distribution of the sampled rows matches the distribution of the weights. When `weighted` is
            set to True, you are no longer guaranteed that every row in the table will be sampled in a single epoch,
            even if all weights are equal.
        :param shuffle: If False, the valid indices will be returned in sequential order. A value of False is mutually
            exclusive with the `weighted` flag.
        :param repeat_by_weight: If True, the sampler will repeat the indices based on the weights. This is useful for
            ensuring that the distribution of the sampled rows matches the distribution of the weights, while still
            sampling every row in the table (with weight > 1) in a single epoch. The number of repeats of samples with
            fractional weights will be determined probabilistically. A value of True will set the length of the sampler
            (and thus an epoch) to the sum of the weights. This flag requires values of `True` for both `weighted` and
            `exclude_zero_weights`.
        :returns: A Sampler based on the weights column of the table."""
    def map(self, func: Callable[[Any], object]) -> Table:
        """Add a function to the list of functions to be applied to each sample in the table before it is returned
        by the `__getitem__` method *when not doing metrics collection*.

        :param func: The function to apply to each sample when not doing metrics collection.
        :returns: The table with the function added to the list of functions to apply to each sample when not doing
            metrics collection.
        """
    def map_collect_metrics(self, func: Callable[[Any], object]) -> Table:
        """Add a function to the list of functions to be applied to each sample in the table before it is returned
        by the `__getitem__` method *when doing metrics collection*. If this list is empty, the `map` functions will be
        used instead.

        :param func: The function to apply to each sample when doing metrics collection.
        :returns: The table with the function added to the list of functions to apply to each sample when doing metrics
            collection.
        """
    def clear_maps(self) -> None:
        """Clear any maps added to the table."""
    @staticmethod
    def from_url(url: Url | str) -> Table:
        """Create a table from a url.

        :param url: The url to create the table from
        :returns: A concrete Table subclass

        :raises ValueError: If the url does not point to a table.
        :raises FileNotFoundError: If the url cannot be found.
        """
    @staticmethod
    def from_names(table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None) -> Table:
        """Create a table from the names specifying its url.

        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url.
        :returns: The table at the resulting url.
        """
    @staticmethod
    def from_torch_dataset(dataset: TorchDataset, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, all_arrays_are_fixed_size: bool = False, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromTorchDataset:
        """Create a Table from a Torch Dataset.

        :param dataset: The Torch Dataset to create the table from.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param all_arrays_are_fixed_size: Whether all arrays (tuples, lists, etc.) in the dataset are fixed size.
            This parameter is only used when generating a SampleType from a single sample in the dataset when no
            `structure` is provided.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromTorchDataset instance.
        """
    @staticmethod
    def from_pandas(df: pd.DataFrame, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromPandas:
        """Create a Table from a Pandas DataFrame.

        :param df: The Pandas DataFrame to create the table from.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromPandas instance.
        """
    @staticmethod
    def from_dict(data: Mapping[str, object], structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromPydict:
        """Create a Table from a dictionary.

        :param data: The dictionary to create the table from.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromPydict instance.
        """
    @staticmethod
    def from_csv(csv_file: str | Path | Url, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromCsv:
        """Create a Table from a .csv file.

        :param csv_file: The url of the .csv file.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromCsv instance.
        """
    @staticmethod
    def from_coco(annotations_file: str | Path | Url, image_folder: str | Path | Url | None = None, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, include_iscrowd: bool = False, keep_crowd_annotations: bool = True, task: Literal['detect', 'segment', 'pose'] = 'detect', segmentation_format: Literal['polygons', 'masks'] | None = None, points: list[float] | None = None, point_attributes: ValueMapLike | None = None, lines: list[int] | None = None, line_attributes: ValueMapLike | None = None, triangles: list[int] | None = None, triangle_attributes: ValueMapLike | None = None, flip_indices: list[int] | None = None, oks_sigmas: list[float] | None = None, per_instance_schemas: dict[str, Schema] | None = None, *, table_url: Url | Path | str | None = None) -> TableFromCoco:
        '''Create a Table from a COCO annotations file.

        :param annotations_file: The url of the COCO annotations file.
        :param image_folder: The url of the folder containing the images referenced in the COCO annotations file. If not
            provided, the image paths in the annotations file will be assumed to either be absolute OR relative to the
            annotations file.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param include_iscrowd: Whether to include the per-instance iscrowd flag in the table rows.
        :param keep_crowd_annotations: Whether to include annotations with `iscrowd=1` in the Table.
        :param task: The task of the dataset. Can be either \'detect\', \'segment\', or \'pose\'.
        :param segmentation_format: The format of the segmentation. Can be either \'polygons\' or \'masks\'.
        :param points: Default keypoint coordinates, used for drawing new instances in the Dashboard. Pose only.
        :param point_attributes: Attributes for each keypoint (e.g. name or color). Pose only.
        :param lines: Default skeleton topology for pose. Will override the skeleton provided in the annotations file.
            Pose only.
        :param line_attributes: Attributes for each line (e.g. name or color). Pose only.
        :param triangles: Triangles for pose.
        :param triangle_attributes: Attributes for each triangle (e.g. name or color). Pose only.
        :param flip_indices: Flip indices for pose.
        :param oks_sigmas: OKS sigmas for pose.
        :param per_instance_schemas: Schemas for any additional metadata to store per instance, e.g. "area" or "id".
            These values should be present in every annotation in the annotations file and match the schema provided.
            Currently only supported for task \'pose\'.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}

        :returns: A TableFromCoco instance.
        '''
    @staticmethod
    def from_parquet(parquet_file: str | Path | Url, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromParquet:
        """Create a Table from a Parquet file.

        :param parquet_file: The url of the Parquet file.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromParquet instance.
        """
    @staticmethod
    def from_ndjson(ndjson_file: str | Path | Url, structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromNdjson:
        """Create a Table from a NDJSON file.

        :param ndjson_file: The url of the NDJSON file.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}.

        :returns: A TableFromNdjson instance.
        """
    @staticmethod
    def from_yolo_ndjson(ndjson_file: str | Path | Url, image_folder: str | Path | Url | None = None, split: str = 'train', table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromYoloNdjson:
        """Create a Table from a YOLO NDJSON file.

        The first line is required to contain the 'class_names' and 'task' keys, and the rest of the lines are required
        to contain the 'file', 'width', 'height', 'split' and 'annotations' keys.

        :param ndjson_file: The url of the NDJSON file.
        :param image_folder: The folder containing the images, used to handle relative paths. If not provided, relative
            image paths are made absolute with respect to the NDJSON file directory.
        :param split: The split to load from the dataset. Rows with 'split' equal to this value will be loaded.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table. If not provided, the description is set to the one in the first
            line of the NDJSON file, or an empty string.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}.

        :returns: A TableFromYoloNdjson instance.
        """
    @staticmethod
    def from_yolo(dataset_yaml_file: str | Path | Url, split: str = 'train', datasets_dir: str | Path | Url | None = None, override_split_path: str | Path | Url | Iterable[str | Path | Url] | None = None, task: Literal['detect', 'segment', 'pose', 'obb'] = 'detect', structure: _SampleTypeStructure | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, points: list[float] | None = None, point_attributes: ValueMapLike | None = None, lines: list[int] | None = None, line_attributes: ValueMapLike | None = None, triangles: list[int] | None = None, triangle_attributes: ValueMapLike | None = None, flip_indices: list[int] | None = None, oks_sigmas: list[float] | None = None, *, table_url: Url | Path | str | None = None) -> TableFromYolo:
        """Create a Table from a YOLO annotations file.

        :param dataset_yaml_file: The url of the YOLO dataset .yaml file.
        :param split: The split to load from the dataset.
        :param datasets_dir: If `path` in the dataset_yaml_file is relative, this directory will be prepended to it. Not
            used if `path` is absolute. If `path` is relative and datasets_dir is not provided, an error is raised.
        :param override_split_path: If provided, this will be used as the path to the directory with images and labels
            instead of the one specified in the dataset_yaml_file. Can be an iterable of such paths.
        :param task: The task of the dataset. Can be either 'detect', 'segment', 'pose', or 'obb'.
        :param structure: The structure of a single sample in the table. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the table.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param points: (Pose estimation only) Optional list default points for the keypoints, relative to a unit square.
            This value will be used when drawing new keypoint instances in the Dashboard.
        :param point_attributes: (Pose estimation only) Optional list of point attributes used to label the keypoints
            , e.g names.
        :param lines: (Pose estimation only) Optional list of keypoints that should be connected by lines. Formatted as
            a flat list of vertexes.
        :param line_attributes: (Pose estimation only) Optional list of line attributes used to label the lines.
        :param triangles: (Pose estimation only) Optional list of vertices that should be connected by lines. Formatted
            as a flat list of vertexes.
        :param triangle_attributes: (Pose estimation only) Optional list of triangle attributes used to label the
            triangles.
        :param flip_indices: (Pose estimation only) Optional list of flip indices used to flip the keypoints.
        :param oks_sigmas: (Pose estimation only) Optional list of OKS sigmas used to compute the OKS metric.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}

        When `task` is `pose`, values for `points`, `point_attributes`, `lines`, `line_attributes`, `triangles`,
        `triangle_attributes`, `oks_sigmas` and `flip_indices` can be provided directly in the YOLO yaml file. Any
        provided constructor arguments will take precedence over values in the yaml file.

        :returns: A TableFromYolo instance.
        """
    @staticmethod
    def from_hugging_face(path: str, name: str | None = None, split: str = 'train', table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> TableFromHuggingFace:
        """Create a Table from a Hugging Face Hub dataset, similar to the `datasets.load_dataset` function.

        :param path: Path or name of the dataset to load, same as in `datasets.load_dataset`.
        :param name: Name of the dataset to load, same as in `datasets.load_dataset`.
        :param split: The split to load, same as in `datasets.load_dataset`.
        :param table_name: The name of the table. If not provided, the `table_name` is set to `split`.
        :param dataset_name: The name of the dataset. If not provided, `dataset_name` is set to `path` if `name` is
            not provided, or to `{path}-{name}` if `name` is provided.
        :param project_name: The name of the project. If not provided, `project_name` is set to `hf-{path}`.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with
            {root_url, project_name, dataset_name, table_name}

        :returns: A TableFromHuggingFace instance.

        """
    @staticmethod
    def from_image_folder(root: str | Path | Url, image_column_name: str = 'image', label_column_name: str = 'label', include_label_column: bool = True, extensions: str | tuple[str, ...] | None = None, table_name: str | None = None, dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, label_overrides: dict[str, MapElement | str] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | Path | str | None = None) -> Table:
        """Create a Table from an image folder.

        This function can be used to load a folder containing subfolders where each subfolder represents a label, or to
        recursively load all matching images in a folder structure without labels. It extends the functionality of
        [torchvision.datasets.ImageFolder](inv:torchvision#torchvision.datasets.ImageFolder).

        When `include_label_column` is True, the dataset elements are returned as tuples of a `PIL.Image` and the
        integer class label. When `include_label_column` is False, `PIL.Image`s are returned without labels. In this
        case, `root` will be recursively scanned.

        :param root: The root directory of the image folder.
        :param image_column_name: The name of the column containing the images.
        :param label_column_name: The name of the column containing the class labels.
        :param include_label_column: Whether to include a column of class labels in the table.
        :param extensions: A list of allowed image extensions. If not provided, a default list of image extensions is
            used.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param label_overrides: A sparse mapping of class names (the directory names) to new class names. A new class
            name can be a string with the new class name or a {class}`MapElement<tlc.core.schema.MapElement>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}
        """
    @staticmethod
    def join_tables(tables: Sequence[Table] | Sequence[Url | str | Path], table_name: str = ..., dataset_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', add_weight_column: bool = True, description: str | None = None, extra_columns: dict[str, _SampleTypeStructure] | None = None, input_tables: list[Url | str | Path] | None = None, weight_column_value: float = 1.0, *, table_url: Url | str | Path | None = None) -> Table:
        """Join multiple tables into a single table.

        The tables will be joined vertically, meaning that the rows of the resulting table will be the concatenation of
        the rows of the input tables, in the order they are provided.

        The schemas of the tables must be compatible for joining. If the tables have different schemas, the schemas will
        be attempted merged, and an error will be raised if this is not possible.

        :param tables: A list of Table instances to join.
        :param table_name: The name of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param root_url: The root url of the table.
        :param if_exists: What to do if the table already exists at the provided url.
        :param add_weight_column: Whether to add a column of sampling weights to the table.
        :param description: A description of the table.
        :param extra_columns: A dictionary of extra columns to add to the table. The keys are the column names, and the
            values are the structures of the columns. These can typically be expressed as
            {func}`Schemas<tlc.core.schema.Schema>`, {func}`ScalarValues<tlc.core.schema.ScalarValue>`, or
            {func}`SampleTypes<tlc.client.sample_type.SampleType>`.
        :param weight_column_value: The value to initialize the weight column with if `add_weight_column` is True.
        :param table_url: A custom Url for the table, mutually exclusive with {root_url, project_name, dataset_name,
            table_name}
        """

def sort_tables_chronologically(tables: list[Table], reverse: bool = False) -> list[Table]:
    """Sort a list of tables chronologically.

    :param tables: A list of tables to sort chronologically.

    :returns: A list of tables sorted chronologically.
    """
def squash_table(table: Table | Url, output_url: Url) -> Table:
    '''Create a copy of this table where all lineage is squashed.

    :Example:
    ```python
    table_instance = Table()
    ... # working
    squashed_table = squash_table(table_instance, Url("s3://bucket/path/to/table"))
    ```

    :param table: The table to squash.
    :param output_url: The output url for the squashed table.

    :returns: The squashed table.
    '''
