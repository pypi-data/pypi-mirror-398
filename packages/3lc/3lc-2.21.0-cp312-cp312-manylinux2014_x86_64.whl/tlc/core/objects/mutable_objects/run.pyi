from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import EXAMPLE_ID as EXAMPLE_ID, FOREIGN_TABLE_ID as FOREIGN_TABLE_ID, RUN_STATUS as RUN_STATUS, RUN_STATUS_CANCELLED as RUN_STATUS_CANCELLED, RUN_STATUS_COLLECTING as RUN_STATUS_COLLECTING, RUN_STATUS_COMPLETED as RUN_STATUS_COMPLETED, RUN_STATUS_EMPTY as RUN_STATUS_EMPTY, RUN_STATUS_PAUSED as RUN_STATUS_PAUSED, RUN_STATUS_POST_PROCESSING as RUN_STATUS_POST_PROCESSING, RUN_STATUS_RUNNING as RUN_STATUS_RUNNING
from tlc.core.builtins.constants.string_roles import STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.builtins.schemas import ExampleIdSchema as ExampleIdSchema, ForeignTableIdSchema as ForeignTableIdSchema
from tlc.core.builtins.types import MetricData as MetricData, MetricTableInfo as MetricTableInfo
from tlc.core.object import Object as Object
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.objects.table import Table as Table
from tlc.core.project_context import ProjectContext as ProjectContext
from tlc.core.schema import DictValue as DictValue, DimensionNumericValue as DimensionNumericValue, Float64Value as Float64Value, Int64Value as Int64Value, MapElement as MapElement, Schema as Schema, StringValue as StringValue
from tlc.core.url import Scheme as Scheme, Url as Url
from tlc.core.utils.object_lock import tlc_object_lock as tlc_object_lock
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from typing import Any, Literal

logger: Incomplete

class Run(MutableObject):
    """Represents a single execution of a specific process or experiment.

    :::{warning}
    Do not instantiate this class directly. Use one of the `Run.from_*` methods or
    {func}`tlc.init()<tlc.client.session.init>` instead.
    :::

    A Run object encapsulates details about its setup, execution, metadata, and metrics.

    Run objects are mutable, allowing for updates to run attributes as they progress or as additional information
    becomes available.
    """
    description: str
    project_name: Incomplete
    metrics: Incomplete
    constants: Incomplete
    status: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, last_modified: str | None = None, description: str | None = None, metrics: list[dict[str, Any]] | None = None, constants: dict[str, Any] | None = None, status: float | None = None, init_parameters: Any = None) -> None:
        """Create a Run object.

        :param description: The description of the run.
        :param metrics: A list of metrics captured during this run.
        :param constants: Constant values used during this run.
        :param status: The status of the run.
        """
    def copy(self, run_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_exists: Literal['raise', 'rename', 'overwrite'] = 'raise', *, destination_url: Url | None = None) -> Run:
        """Create a copy of this run.

        The copy is performed to:
          1. A URL derived from the given run_name, project_name, and root_url if given
          2. destination_url, if given
          3. A generated URL derived from the run's URL, if none of the above are given

        :param run_name: The name of the run to create.
        :param project_name: The name of the project to create the run in.
        :param root_url: The root URL to create the run in.
        :param if_exists: What to do if the destination URL already exists.
        :param destination_url: The URL to copy the run to.
        :return: The copied run.
        """
    @property
    def name(self) -> str:
        """The name of the run."""
    def add_input_table(self, input_table: Table | Url | str) -> None:
        """Adds an input table to the run.

        This updates the Run object to include the input table in the list of inputs to the Run.

        :param input_table: The input table to add.
        """
    def add_input_value(self, input_value: dict[str, Any]) -> None:
        """Adds a value to the inputs of the run.

        :param input_value: The value to add.
        """
    def add_output_value(self, output_value: dict[str, Any]) -> None:
        """Adds a value to the outputs of the run.

        :param output_value: The value to add.
        """
    def set_parameters(self, parameters: dict[str, Any]) -> None:
        """Set the parameters of the run.

        :param parameters: The parameters to set.
        """
    def set_description(self, description: str) -> None:
        """Set the description of the run.

        :param description: The description to set.
        """
    @staticmethod
    def from_url(url: Url | str) -> Run:
        """Creates a Run instance from the URL of an existing Run.

        :param url: The URL to the Run object.

        :return: The Run object.
        """
    @staticmethod
    def from_names(run_name: str | None = None, project_name: str | None = None, root_url: Url | str | None = None) -> Run:
        """Creates a Run instance from the names specifying the URL of an existing Run.

        :param run_name: The name of the run.
        :param project_name: The name of the project.
        :param root_url: The root url to use instead of the default root url.

        :return: The Run at the resulting url.
        """
    @property
    def metrics_tables(self) -> list[Table]:
        """
        Returns a list of the metrics tables for this run.
        """
    @property
    def bulk_data_url(self) -> Url:
        """
        Returns the URL of the bulk data for this run.
        """
    def reduce_embeddings_by_foreign_table_url(self, foreign_table_url: Url | str, delete_source_tables: bool = True, **kwargs: Any) -> dict[Url, Url]:
        """Reduces all metrics tables in a Run using a reducer trained on the embeddings in a specified metrics table.

        See
        {func}`tlc.reduce_embeddings_by_foreign_table_url<tlc.client.reduce.reduce.reduce_embeddings_by_foreign_table_url>`
        for more information.

        :param foreign_table_url: The Url of the foreign table to use for reduction.
        :param delete_source_tables: If True, the source metrics tables will be deleted after reduction.

        :returns: A dictionary mapping the original table URLs to the reduced table URLs.
        """
    def reduce_embeddings_per_dataset(self, delete_source_tables: bool = True, **kwargs: Any) -> dict[Url, Url]:
        """
        Reduces the embeddings for each dataset in this run.

        See
        {func}`tlc.reduce_embeddings_per_dataset<tlc.client.reduce.reduce.reduce_embeddings_per_dataset>`
        for more information.

        :param delete_source_tables: If True, the source metrics tables will be deleted after reduction.

        :returns: A dictionary mapping the original table URLs to the reduced table URLs.
        """
    def update_metrics(self, metric_infos: list[MetricTableInfo] | None = None) -> None:
        """Add new metrics to the run.

        Any metrics that are already present in the run will not be added again.

        :param metric_infos: A list of MetricTableInfo dicts to add to the run.
        """
    def add_metrics_table(self, metrics_table: Table | Url) -> None:
        """Add a metrics table to the run.

        :param metrics_table: The metrics table to add.
        """
    def add_metrics(self, metrics: dict[str, MetricData], column_schemas: dict[str, Schema] | None = None, foreign_table_url: Url | str | None = None, foreign_table_display_name: str = '', constants: dict[str, Any] | None = None) -> list[MetricTableInfo]:
        '''Write the provided metrics to a Table and associate it with the run.

        :param metrics: The metrics data (dict of column names to column data) to write.
        :param column_schemas: The schemas for the metrics data.
        :param foreign_table_url: The URL of the table to associate with the metrics data. If provided, the metrics data
            will be augmented with extra columns to identify the example ID and the foreign table, if these columns are
            not already present. If the metrics data does not correspond 1-to-1 with the table, ensure the metrics data
            includes an "example_id" column.
        :param foreign_table_display_name: The display name of the foreign table to show in the Dashboard.
        :param constants: The constants to add to the run.
        :returns: The written table info.

        :raises ValueError: If the number of rows in the metrics data does not match the number of rows in the table, or
            the input_table_url is not a valid URL.
        :raises FileNotFoundError: If the input_table_url can not be found.
        '''
    def add_metrics_data(self, metrics: dict[str, MetricData], override_column_schemas: dict[str, Schema] | None = None, input_table_url: Url | str | None = None, table_writer_base_name: str = 'metrics', stream_name: str = '') -> list[MetricTableInfo]:
        '''Write the given metrics to a Table and updates the run with the table info.

        :param metrics: The metrics data (dict of column-names to columns) to write.
        :param override_column_schemas: A dictionary of schemas to override the default schemas for the columns.
        :param input_table_url: The URL of the table to associate with the metrics data. If provided, the metrics data
            will be augmented with extra columns to identify the example ID and the foreign table, if these columns are
            not already present. If the metrics data does not correspond 1-to-1 with the table, ensure the metrics data
            includes an "example_id" column.
        :param table_writer_base_name: The base name of the written tables.
        :param table_writer_key: A key used to further identify the written tables.

        :returns: The written table infos.

        :raises ValueError: If the number of rows in the metrics data does not match the number of rows in the table, or
            the input_table_url is not a valid URL.
        :raises FileNotFoundError: If the input_table_url can not be found.
        '''
    def set_status_running(self) -> None:
        """Set the status of the run to running."""
    def set_status_collecting(self) -> None:
        """Set the status of the run to collecting."""
    def set_status_post_processing(self) -> None:
        """Set the status of the run to post processing."""
    def set_status_completed(self) -> None:
        """Set the status of the run to completed."""
    def set_status_empty(self) -> None:
        """Set the status of the run to empty."""
    def set_status_paused(self) -> None:
        """Set the status of the run to paused."""
    def set_status_cancelled(self) -> None:
        """Set the status of the run to cancelled."""
