from collections.abc import Callable as Callable
from lightning.pytorch.core.module import LightningModule as LightningModule
from tlc.client.sample_type import _SampleTypeStructure
from tlc.client.session import init as init
from tlc.client.torch.metrics.collect import collect_metrics as collect_metrics
from tlc.client.torch.metrics.metrics_collectors import MetricsCollectorType as MetricsCollectorType
from tlc.client.torch.metrics.predictor import Predictor as Predictor, PredictorArgs as PredictorArgs
from tlc.core.builtins.constants.column_names import RUN_STATUS as RUN_STATUS, RUN_STATUS_COMPLETED as RUN_STATUS_COMPLETED, RUN_STATUS_RUNNING as RUN_STATUS_RUNNING
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.from_python_object.table_from_torch_dataset import TableFromTorchDataset as TableFromTorchDataset
from tlc.core.url import Url as Url
from torch.nn import Module as Module
from typing import Literal

def lightning_module(structure: _SampleTypeStructure | None = None, dataset_prefix: str = '', run_name: str | None = None, run_description: str | None = None, project_name: str | None = None, root_url: Url | str | None = None, if_dataset_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'reuse', if_run_exists: Literal['raise', 'reuse', 'rename', 'overwrite'] = 'rename', add_weight_column: bool = True, all_arrays_are_fixed_size: bool = True, exclude_zero_weights_train: bool = True, weighted: bool = True, use_latest: bool = True, map_functions: list[Callable[[object], object]] | Callable[[object], object] | None = None, predictor_args: PredictorArgs | None = None, metrics_collectors: MetricsCollectorType | None = None, collect_metrics_on_train_end: bool = True, collect_metrics_on_train_start: bool = False, metrics_collection_interval: int = 0, metrics_collection_start: int = 0, metrics_collection_exclude_zero_weights: bool = True, metrics_collection_map_functions: list[Callable[[object], object]] | Callable[[object], object] | None = None) -> Callable[[type[LightningModule]], type[LightningModule]]:
    '''Decorator for using 3LC with PyTorch Lightning.

    Adding this decorator to a [LightningModule](inv:pytorch_lightning#lightning.pytorch.core.module.LightningModule)
    subclass definition will create tables from the datasets used within the module, as well as collect metrics and
    create a run when used with a [Trainer](inv:pytorch_lightning#common/trainer).

    :param structure: The structure of a single sample in the datasets. This is used to infer the schema of the table,
            and perform any necessary conversions between the row representation and the sample representation of the
            data. If not provided, the structure will be inferred from the first sample in the dataset.
    :param dataset_prefix: A prefix to be added to each split of the dataset to create dataset names.
    :param run_name: The name of the run.
    :param run_description: The description of the run.
    :param project_name: The name of the project.
    :param root_url: The root url of the table.
    :param if_dataset_exists: What to do if the dataset already exists. One of "raise", "reuse", "rename", "overwrite".
    :param if_run_exists: What to do if the run already exists. One of "raise", "reuse", "rename", "overwrite".
    :param add_weight_column: Whether to add a column of sampling weights to the table, all initialized to 1.0.
    :param all_arrays_are_fixed_size: Whether all arrays (tuples, lists, etc.) in the dataset are fixed size. This
        parameter is only used when generating a SampleType from a single sample in the dataset when no `structure` is
        provided.
    :param exclude_zero_weights_train: If True, rows with a weight of zero will be excluded from the sampler during
        training. This is useful for adjusting the length of the sampler, and thus the length of an epoch, to the number
        of non-zero weighted rows in the table.
    :param weighted: If True, the sampler will use sample weights (beyond the exclusion of zero-weighted rows) to ensure
        that the distribution of the sampled rows matches the distribution of the weights. When `weighted` is set to
        True, you are no longer guaranteed that every row in the table will be sampled in a single epoch, even if all
        weights are equal.
    :param use_latest: If True, the latest versions of all tables will be used.
    :param map_functions: A list of map functions to be applied to all tables, except when collecting metrics.
    :param metrics_collectors: List of metrics collectors to be used to collect metrics.
    :param collect_metrics_on_train_end: Whether to collect metrics at the end of training.
    :param collect_metrics_on_train_start: Whether to collect metrics at the start of training.
    :param metrics_collection_interval: The number of epochs between each metrics collection. A value of 0 means that
        metrics will not be collected.
    :param metrics_collection_start: The epoch to start collecting metrics. Metrics will be collected at the end of the
        specified epochs.
    :param metrics_collection_exclude_zero_weights: Whether to exclude zero-weighted samples when collecting metrics.
    :param metrics_collection_map_functions: A list of map functions to be applied to all tables when collecting
        metrics.
    '''
