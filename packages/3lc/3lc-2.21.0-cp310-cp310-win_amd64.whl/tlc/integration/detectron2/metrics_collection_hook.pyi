import torch
from _typeshed import Incomplete
from detectron2.config import CfgNode as CfgNode
from detectron2.engine.hooks import HookBase
from tlc.client.helpers import active_run as active_run
from tlc.client.torch.metrics.collect_dataset import collect_metrics as collect_metrics
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import Predictor as Predictor
from tlc.core.builtins.constants.column_names import RUN_STATUS as RUN_STATUS, RUN_STATUS_CANCELLED as RUN_STATUS_CANCELLED, RUN_STATUS_COMPLETED as RUN_STATUS_COMPLETED, RUN_STATUS_RUNNING as RUN_STATUS_RUNNING
from tlc.core.builtins.schemas.schemas import EpochSchema as EpochSchema, IterationSchema as IterationSchema
from torch.utils.data import DataLoader as DataLoader

msg: str
logger: Incomplete

class MetricsCollectionHook(HookBase):
    '''Hook that periodically collects metrics on a detectron dataset.

    The hook will collect metrics on the dataset specified by `dataset_name`, which must be registered in the
    MetadataCatalog (see the {doc}`detectron2 docs<detectron2:tutorials/datasets>`
    for more details). The metrics will be collected using the metrics collectors specified in `metrics_collectors`.

    The hook can be configured to collect metrics at the beginning of training, at regular intervals during training,
    and at the end of training. The frequency of metric collection can be set with `collection_frequency`, and the
    iteration to start collecting metrics can be set with `collection_start_iteration`.

    Metrics will be collected _after_ an iteration is completed.

    :example:
    ```python
    # Setup detectron2 trainer and register datasets
    trainer = ...

    # Collect metrics on the training set before and after training:

    train_hook = MetricsCollectionHook(
        dataset_name="my_train_dataset",
        metrics_collectors=MyMetricsCollector(),
        collect_metrics_before_train=True,
        collect_metrics_after_train=True,
    )

    # Collect metrics on the validation set every 100 iterations starting at iteration 1000:
    test_hook = MetricsCollectionHook(
        dataset_name="my_test_dataset",
        metrics_collectors=MyMetricsCollector(),
        collection_start_iteration=1000,
        collection_frequency=100,
    )

    trainer.register_hooks([train_hook, test_hook])
    trainer.train()
    ```
    '''
    def __init__(self, dataset_name: str, metrics_collectors: list[MetricsCollector] | MetricsCollector, predictor: torch.nn.Module | Predictor | None = None, cfg: CfgNode | None = None, collection_start_iteration: int = 0, collection_frequency: int = -1, collect_metrics_before_train: bool = False, collect_metrics_after_train: bool = False, metric_collection_batch_size: int = 8, dataset_split: str = '') -> None:
        """Initializes the hook

        :param dataset_name: The name of the dataset to collect metrics on. This name should be registered in the
            detectron2 MetadataCatalog.
        :param metrics_collectors: The metrics collector(s) to use.
        :param predictor: A model or Predictor to use for computing metrics.
        :param cfg: The detectron config. If None, the config will be loaded from the trainer.
        :param collection_start_iteration: The iteration to start collecting metrics on.
        :param collection_frequency: The frequency with which to collect metrics. Must be greater than 0 for metrics to
            be collected during training.
        :param collect_metrics_before_train: Whether to collect metrics at the beginning of training.
        :param collect_metrics_after_train: Whether to collect metrics at the end of training.
        :param metric_collection_batch_size: The batch size to use for collecting metrics.
        :param dataset_split: The split of the dataset to collect metrics on. Will be prepended to the dataset name for
            any aggregate metric values collected by the hook.
        """
    def before_train(self) -> None:
        """Creates a test-dataloader from the trainer and collects metrics if required."""
    def after_train(self) -> None:
        """Collects metrics if required."""
    def after_step(self) -> None:
        """Collects 3LC metrics at regular intervals."""
    @property
    def model(self) -> torch.nn.Module:
        """Returns the model from the trainer."""
