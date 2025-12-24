import torch
from tlc.client.helpers import active_run as active_run
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollector as MetricsCollector
from tlc.client.torch.metrics.predictor import Predictor as Predictor, PredictorOutput as PredictorOutput
from tlc.client.utils import batched_iterator as batched_iterator
from tlc.core.builtins.constants.column_names import EXAMPLE_ID as EXAMPLE_ID, RUN_STATUS as RUN_STATUS, RUN_STATUS_COLLECTING as RUN_STATUS_COLLECTING, RUN_STATUS_RUNNING as RUN_STATUS_RUNNING
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from tlc.core.writers.metrics_writer import MetricsTableWriter as MetricsTableWriter
from torch.utils.data import DataLoader, Dataset as Dataset
from typing import Any, Callable, ClassVar

inference_mode: Callable

def collect_metrics(table: Dataset, metrics_collectors: list[MetricsCollector], predictor: torch.nn.Module | Predictor | None = None, constants: dict[str, Any] | None = None, constants_schemas: dict[str, Schema] | None = None, dataset_url: str = '', dataset_name: str = '', run_url: Url | str | None = None, collect_aggregates: bool = True, split: str = '', exclude_zero_weights: bool = False, *, dataloader_args: dict[str, Any] | None = None) -> None:
    '''Collect per-sample metrics with a PyTorch Dataset.

    + Writes a single metrics table which uses the input table as foreign table. This table will contain any constants
      contained in the `constants` argument, as well as any metrics computed by the metrics collectors.
    + Add the metadata of the metrics table to the `metrics` property of the Run.
    + Add the Url of the input table to the Run as an input.
    + Collect aggregate values from the metrics collectors and add them to the Run (merged with the constants)

    :param table: The Dataset to collect metrics from.
    :param metrics_collectors: A list of metrics collectors to use.
    :param predictor: A model or Predictor to use for computing metrics.
    :param constants: A dictionary of constants to use when collecting metrics.
    :param constants_schemas: A dictionary of schemas for the constants. If no schemas are provided, the schemas will be
        inferred from the constants.
    :param dataset_url: The url of the dataset.
    :param dataset_name: The name of the dataset.
    :param run_url: The url of the run to add the metrics to. If not specified, the active run will be used.
    :param collect_aggregates: Whether to collect aggregate values from the metrics collectors and add them to the Run.
        This allows an aggregate view to be shown in the Project page of the 3LC Dashboard. Aggregate values are
        computed for all computable columns in the metrics collectors, and are prefixed with the split name. For
        example, if a metrics collector defines a computable column called "accuracy", and the split is "train", then
        the aggregate value will be called "train_accuracy_avg".
    :param split: The split of the dataset. This will be prepended to the aggregate metric names.
    :param dataloader_args: Additional arguments to pass to the dataloader.
    '''

class _DataLoaderManager:
    created_dataloaders: ClassVar[dict[str, DataLoader]]
    @classmethod
    def get_or_create_torch_dataloader(cls, table: Dataset, dataset_url: str, dataloader_args: dict[str, Any] | None = None) -> DataLoader: ...
