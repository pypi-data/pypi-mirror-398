from _typeshed import Incomplete
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_table.dimensional_reduction_table import _DimensionalReductionTable
from tlc.core.schema import Float32Value as Float32Value, Int32Value as Int32Value, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

msg: str
umap: Incomplete
logger: Incomplete

class UMAPTable(_DimensionalReductionTable):
    """
    A procedural table where a column in the input table column has been has dimensionally reduced by the UMAP
    algorithm.

    """
    algorithm_name: str
    n_neighbors: int
    metric: str
    min_dist: float
    n_jobs: int
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, input_table_url: Url | Table | None = None, source_embedding_column: str | None = None, target_embedding_column: str | None = None, retain_source_embedding_column: bool | None = None, standard_scaler_normalize: bool | None = None, n_components: int | None = None, n_neighbors: int | None = None, metric: str | None = None, min_dist: float | None = None, n_jobs: int | None = None, fit_table_url: Table | Url | None = None, model_url: Url | None = None, init_parameters: Any = None, random_state: int | None = None, input_tables: list[Url] | None = None) -> None:
        """Creates a derived table with an (additional) UMAP-ed column based on input column and wanted dimensionality.

        :param input_table_url: The input table to apply UMAP to
        :param source_embedding_column: The column in the input table to apply UMAP to
        :param target_embedding_column: The name of the new column to create in the output table
        :param retain_source_embedding_column: Whether to retain the source column in the UMAP table, defaults to False
        :param standard_scaler_normalize: Whether to apply the sklearn standard scaler to input before mapping,
            defaults to False
        :param n_components: The dimension of the output embedding
        :param n_neighbors: The number of neighbors to use to approximate the manifold structure
        :param metric: The metric to use to compute distances in high dimensional space
        :param min_dist: The minimum distance between points in the low dimensional embedding
        :param n_jobs: The number of threads to use for the reduction. If set to anything other than 1, the random_state
            parameter of the UMAP algorithm is set to None, which means that the results will not be deterministic.
        :param fit_table_url: The table to use for fitting the UMAP transform, if not specified the input table is used
        :param model_url: The URL to store/load the UMAP model file. If empty, no model is saved.
        :param random_state: The random state to use for the reduction
        """
    @property
    def seed(self) -> list[int]: ...
