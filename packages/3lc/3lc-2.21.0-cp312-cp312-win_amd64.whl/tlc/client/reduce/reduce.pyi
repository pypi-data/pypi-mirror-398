from _typeshed import Incomplete
from tlc.client.reduce.reduction_method import ReducerArgs as ReducerArgs, ReductionMethod as ReductionMethod
from tlc.core.objects.table import Table as Table, sort_tables_chronologically as sort_tables_chronologically
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

def create_reducer(method: str, reducer_args: ReducerArgs | None = None) -> ReductionMethod:
    """Create a reduction method object.

    :param method: The reduction method to use.
    :param reducer_args: Arguments specific to the reduction method, e.g.
        {func}`UMapTableArgs<tlc.client.reduce.umap.UMapTableArgs>`.

    :returns: A reduction method object.
    """
def reduce_embeddings(tables: Table | list[Table], method: str = 'umap', delete_source_tables: bool = False, **kwargs: Any) -> Table | dict[Url, Url]:
    """Reduce all embeddings columns in the input table(s).

    The reduction method is fit and applied to each table independently.

    :param tables: A Table (or a list of tables) to reduce.
    :param method: The reduction method to use.
    :param delete_source_tables: Specifies whether to delete the source tables after performing the reduction. Enabling
        this option can help minimize disk-space usage.
    :param kwargs: Arguments specific to the reduction method, see e.g.
        {func}`UMapTableArgs<tlc.client.reduce.umap.UMapTableArgs>` for valid keyword arguments.

    :returns: A single reduced table if the input is a single table, or a dictionary mapping the URLs of the input
        tables to the URLs of the reduced tables.

    :::{Warning} The `tables` argument will be renamed to `table` in the next major release, and passing a list of
        tables will be deprecated. :::

    :::{Warning} Enabling the `delete_source_tables` option will disrupt the lineage of the
        reduced tables. If the cache files for these reduced tables are subsequently deleted, they will be
        irrecoverable.
    :::
    :::{Note} The `delete_source_tables` option should not be enabled if further dimensionality reductions on the same
    input tables are anticipated. :::
    """
def reduce_embeddings_multiple_parameters(table: Table | Url, method: str = 'umap', delete_source_tables: bool = False, parameter_sets: list[dict[str, Any]] | None = None) -> Url:
    """Reduce embeddings using multiple reducer parameter sets.

    This function will add a dimensionality reduced column for each parameter set in `parameter_sets`.
    """
def reduce_embeddings_per_dataset(tables: list[Table], method: str = 'umap', delete_source_tables: bool = False, **kwargs: Any) -> dict[Url, Url]:
    """Reduce embeddings for a stream of tables.

    Will fit a reduction method on the most recent table from each stream, and apply the reduction to all earlier tables
    in the stream. A stream is defined as a sequence of tables with the same example table ID, which means they
    originate from the same dataset.

    Tables with no example table ID will be ignored.

    :param tables: A list of tables to reduce.
    :param method: The reduction method to use.
    :param delete_source_tables: Specifies whether to delete the source tables after performing the reduction. Enabling
        this option can help minimize disk-space usage.
    :param kwargs: Arguments specific to the reduction method, see e.g.
        {func}`UMapTableArgs<tlc.client.reduce.umap.UMapTableArgs>` for valid keyword arguments.

    :returns: A dictionary mapping the URLs of the input tables to the URLs of the reduced tables.

    :::{Warning} Enabling the `delete_source_tables` option will disrupt the lineage of the
        reduced tables. If the cache files for these reduced tables are subsequently deleted, they will be
        irrecoverable.
    :::
    :::{Note} The `delete_source_tables` option should not be enabled if further dimensionality reductions on the same
    input tables are anticipated.
    :::
    """
def reduce_embeddings_by_foreign_table_url(tables: list[Table], foreign_table_url: Url, method: str = 'umap', delete_source_tables: bool = False, **kwargs: Any) -> dict[Url, Url]:
    """Reduce embeddings using a single reducer across all tables.

    The reduction method is fit on the most recently written table in the stream of tables defined by
    `foreign_table_url`, and applied on all other tables.

    For example, this function can be used to train a UMAP model on the embeddings collected from the validation set
    during the final epoch, and then apply that model to the embeddings collected from the training set and validation
    set during all epochs.

    :param tables: A list of tables to reduce.
    :param method: The reduction method to use.
    :param foreign_table_url: Identifies which stream of metrics tables to use for fitting a reduction model. Must be a
        absolute URL after expanding aliases.
    :param delete_source_tables: Specifies whether to delete the source tables after performing the reduction. Enabling
        this option can help minimize disk-space usage.
    :param kwargs: Arguments specific to the reduction method, see e.g.
        {func}`UMapTableArgs<tlc.client.reduce.umap.UMapTableArgs>` for valid keyword arguments.

    :returns: A dictionary mapping the URLs of the input tables to the URLs of the reduced tables.

    :raises ValueError: If `foreign_table_url` does not identify a stream of tables.

    :::{Warning} Enabling the `delete_source_tables` option will disrupt the lineage of the
        reduced tables. If the cache files for these reduced tables are subsequently deleted, they will be
        irrecoverable.
    :::
    :::{Note} The `delete_source_tables` option should not be enabled if further dimensionality reductions on the same
    input tables are anticipated.
    :::
    """
def reduce_embeddings_with_producer_consumer(producer: Table, consumers: list[Table], method: str = 'umap', delete_source_tables: bool = False, **kwargs: Any) -> dict[Url, Url]:
    """Reduce embeddings for a producer table and a list of consumer tables.

    The reduction method is fit on the producer table, and then applied to the consumer tables.

    :param producer: The table to fit the reduction method on.
    :param consumers: The tables to apply the reduction method to.
    :param method: The reduction method to use.
    :param delete_source_tables: Specifies whether to delete the source tables after performing the reduction. Enabling
        this option can help minimize disk-space usage.
    :param kwargs: Arguments specific to the reduction method, see e.g.
        {func}`UMapTableArgs<tlc.client.reduce.umap.UMapTableArgs>` for valid keyword arguments.

    :returns: A dictionary mapping the URLs of the consumer tables to the URLs of the reduced tables.

    :::{Warning} Enabling the `delete_source_tables` option will disrupt the lineage of the
        reduced tables. If the cache files for these reduced tables are subsequently deleted, they will be
        irrecoverable.
    :::
    :::{Note} The `delete_source_tables` option should not be enabled if further dimensionality reductions on the same
    input tables are anticipated.
    :::
    """
