from _typeshed import Incomplete
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_table.dimensional_reduction_table import _DimensionalReductionTable
from tlc.core.schema import BoolValue as BoolValue, Float32Value as Float32Value, Int32Value as Int32Value, Schema as Schema, StringValue as StringValue
from tlc.core.url import Scheme as Scheme, Url as Url
from typing import Any

msg: str
pacmap: Incomplete
logger: Incomplete

class PaCMAPTable(_DimensionalReductionTable):
    """
    A procedural table where a column in the input table column has been has dimensionally reduced by the PaCMAP
    algorithm.
    """
    algorithm_name: str
    n_neighbors: int
    MN_ratio: float
    FP_ratio: float
    distance: str
    lr: float
    num_iters: int
    verbose: bool
    apply_pca: bool
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, input_table_url: Url | Table | None = None, source_embedding_column: str | None = None, target_embedding_column: str | None = None, retain_source_embedding_column: bool | None = None, fit_table_url: Table | Url | None = None, model_url: Url | None = None, n_components: int | None = None, n_neighbors: int | None = None, MN_ratio: float | None = None, FP_ratio: float | None = None, distance: str | None = None, lr: float | None = None, num_iters: int | None = None, verbose: bool | None = None, apply_pca: bool | None = None, random_state: int | None = None, init_parameters: Any = None, standard_scaler_normalize: bool | None = None, input_tables: list[Url] | None = None) -> None: ...
