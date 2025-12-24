from _typeshed import Incomplete
from detectron2.engine.hooks import HookBase
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.url import Url as Url

msg: str
logger: Incomplete

class UMAPReduceEmbeddingsHook(HookBase):
    """Hook to apply UMAP reduction to embeddings generated during a run.

    Will use the most recently written metrics table in the run to fit a UMAP model.
    This model will then be used to apply dimensionality reduction to all other viable metrics tables collected
    during training. A metrics table is considered viable for reduction if it contains at least one column where the
    schema defines a value with a number role of NUMBER_ROLE_NN_EMBEDDING.

    __Note:__ because of the current design, metrics collection hooks registered with the run will need to
    ensure that the most recent metrics table written to the run is the one that should be used to fit the UMAP
    model. This can be done by ensuring the order of hooks is correct and their collection frequencies are set
    appropriately. This limitation will be made more explicit in the future.

    :param run_url: The URL of the run.
    :param n_components: The number of components to reduce the embeddings to.
    """
    def __init__(self, run_url: str, n_components: int = 3, delete_source_tables: bool = True) -> None:
        """Create a new UMAP reduction hook."""
    def after_train(self) -> None:
        """Perform UMAP reduction on metrics generated during training."""
