from _typeshed import Incomplete
from detectron2.config import CfgNode as CfgNode
from detectron2.engine.hooks import HookBase
from tlc.client.helpers import active_run as active_run
from tlc.core.builtins.schemas.schemas import IterationSchema as IterationSchema
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.schema import Float32Value as Float32Value, Schema as Schema
from tlc.core.url import Url as Url

msg: str
logger: Incomplete

class DetectronMetricsCollectionHook(HookBase):
    """Hook that collects detectron2 standard metrics during training.

    Collect any metrics that are available in the detectron2 event storage and write them as a single table to the run.

    :param run_url: A tlc.Run object, or the URL of the Run to use. Will default to using the current active Run.
    :param cfg: The detectron2 config. If None, the config will be read from the trainer.
    :param collection_start_iteration: The iteration to start collecting metrics on.
    :param collection_frequency: The frequency with which to collect metrics.
    :param collect_metrics_before_train: Indicates whether metrics should be collected at the beginning of training.
        **Note:** This option is deprecated and will be removed in future releases. The hook is intended primarily
        for collecting metrics during the training process, so using this argument is not recommended.
    """
    def __init__(self, run_url: Run | Url | str | None = None, cfg: CfgNode | None = None, collection_start_iteration: int = 0, collection_frequency: int = -1, collect_metrics_before_train: bool = False) -> None: ...
    def before_train(self) -> None:
        """Checks that the detectron config includes the values required to collect metrics, collects metrics if
        required."""
    def after_train(self) -> None:
        """Writes the metrics table to the run."""
    def after_step(self) -> None:
        """Collects metrics if required."""
