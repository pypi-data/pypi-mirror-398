from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import EPOCH as EPOCH, EXAMPLE_ID as EXAMPLE_ID, FOREIGN_TABLE_ID as FOREIGN_TABLE_ID
from tlc.core.builtins.schemas.schemas import EpochSchema as EpochSchema, ExampleIdSchema as ExampleIdSchema, ForeignTableIdSchema as ForeignTableIdSchema
from tlc.core.builtins.types import MetricTableInfo as MetricTableInfo
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from tlc.core.writers.table_writer import TableWriter as TableWriter

logger: Incomplete

class MetricsTableWriter(TableWriter):
    '''A class for writing metrics tables to runs.

    :::{admonition} Updating Runs with Metrics Tables
    A MetricsTableWriter is a specialized
    {class}`TableWriter<tlc.core.writers.table_writer.TableWriter>` that writes tables inside a run\'s directory. The
    MetricsTableWriter does not update the run to reference the newly written tables. To do that, call
    {func}`Run.update_metrics<tlc.core.objects.mutable_objects.run.Run.update_metrics>` with the return value of
    {func}`get_written_metrics_infos<tlc.core.writers.metrics_writer.MetricsTableWriter.get_written_metrics_infos>`.
    :::

    If a `foreign_table_url` is supplied, the written metrics table will also be associated with the given foreign
    table, indicating that each metric value is associated with a specific row in the foreign table.

    For this to work, each added metrics batch must contain a column called `example_id`. This is the foreign key that
    links the metrics table to the foreign table. The values of `example_id` are linear indices into the foreign table,
    starting from 0. A single metrics table can contain multiple values for the same `example_id`, and does not need to
    contain values for all `example_id`s in the foreign table.

    :Example:
    ```python
    from tlc import MetricsTableWriter

    # Assuming a input table of length 8 exists at the url "input_table_url"

    run = tlc.init()

    metrics_writer = MetricsTableWriter(
        run_url=run.url,
        foreign_table_url="input_table_url",
        foreign_table_display_name="Input Table",
    )

    # First batch of metrics, corresponding to the first 4 rows of the foreign table
    metrics_writer.add_batch({
        "loss": [0.1, 0.2, 0.3, 0.4], "example_id": [0, 1, 2, 3],
    })

    # Second batch of metrics, corresponding to the last 4 rows of the foreign table
    metrics_writer.add_batch({
        "loss": [0.2, 0.4, 0.1, 0.5], "example_id": [4, 5, 6, 7],
    })

    # Finalize the metrics writer to write the metrics table to persistent storage
    metrics_table = metrics_writer.finalize()

    # Add a reference to the written metrics table to the run
    run.update_metrics(metrics_writer.get_written_metrics_infos())
    ```
    '''
    run_url: Incomplete
    foreign_table_url: Incomplete
    foreign_table_display_name: Incomplete
    def __init__(self, run_url: Url | str | None = None, foreign_table_url: Url | str = '', foreign_table_display_name: str = '', column_schemas: dict[str, Schema] | None = None) -> None:
        """Initialize a MetricsTableWriter.

        :param run_url: The Url of the run to write metrics for. Will default to the active run if not provided.
        :param foreign_table_url: The Url of the dataset to write metrics for.
        :param foreign_table_display_name: An optional display-name of the foreign table to show in the Dashboard. If
            not provided the dashboard will generate one from the URL.
        :param column_schemas: A dictionary of column names to schema overrides. Schemas will be inferred from the data
            if not provided.
        """
    def get_written_metrics_infos(self) -> list[MetricTableInfo]:
        """Get the list of written metrics infos.

        :return: A list of written metrics infos. The returned Urls are relative to the run's Url.
        """
    def finalize(self) -> Table:
        """Write all added batches to persistent storage and return the written table.

        :return: The written metrics table.
        """
