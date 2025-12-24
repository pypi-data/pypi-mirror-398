from _typeshed import Incomplete
from tlc.client.reduce.reduction_method import ReducerArgs as ReducerArgs, ReductionMethod as ReductionMethod
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_table.pacmap_table import PaCMAPTable as PaCMAPTable
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url

logger: Incomplete

class PaCMAPTableArgs(ReducerArgs, total=False):
    """Arguments specific to the PaCMAP reduction method.

    See {class}`PaCMAPTable<tlc.core.objects.tables.from_table.pacmap_table.PaCMAPTable>` for more information.
    """
    n_components: int
    n_neighbors: int
    MN_ratio: float
    FP_ratio: float
    distance: str
    lr: float
    num_iters: int
    verbose: bool
    apply_pca: bool

class PaCMAPReduction(ReductionMethod[PaCMAPTableArgs]):
    """Perform dimensionality reduction on columns of tables using the PaCMAP algorithm.

    :params reducer_args: A dictionary of arguments which are specific to the reduction method.
    """
    def default_args(self) -> PaCMAPTableArgs:
        """Returns the default arguments for the PaCMAP reduction method."""
    def fit_reduction_method(self, table: Table, column: str) -> Url:
        """Fits a PaCMAPTable and returns the model URL"""
    def apply_reduction_method(self, table: Table, fit_table_url: Url, column: str) -> Url | None: ...
