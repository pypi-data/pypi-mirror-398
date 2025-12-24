import torch
from _typeshed import Incomplete
from super_gradients.common.environment.ddp_utils import multi_process_safe
from super_gradients.training.models.sg_module import SgModule as SgModule
from super_gradients.training.utils.callbacks import Callback, PhaseContext as PhaseContext
from super_gradients.training.utils.predict.prediction_results import ImagePrediction as ImagePrediction, ImagesPredictions as ImagesPredictions
from tlc.client.helpers import active_run as active_run
from tlc.client.session import init as init
from tlc.core.builtins.constants.column_names import EXAMPLE_ID as EXAMPLE_ID
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_NN_EMBEDDING as NUMBER_ROLE_NN_EMBEDDING
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.objects.table import Table as Table
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Schema as Schema
from tlc.core.url import Url as Url
from tlc.core.writers.metrics_writer import MetricsTableWriter as MetricsTableWriter
from tlc.integration.super_gradients.callbacks.embeddings_pipeline import EmbeddingsPipeline as EmbeddingsPipeline
from tlc.integration.super_gradients.callbacks.pipeline_params import PipelineParams as PipelineParams
from torch.nn import Module as Module
from torch.utils.data import Dataset
from typing import Any, Literal

logger: Incomplete

class MetricsCollectionCallback(Callback):
    """Callback that collects per-sample metrics and logs SuperGradients aggregate metrics to a 3LC run.

    To collect per-sample metrics, subclasses must implement the methods `compute_metrics` and
    `metrics_column_schemas`, and the property `label_column_name`.
    """
    project_name: Incomplete
    run_name: Incomplete
    run_description: Incomplete
    image_column_name: Incomplete
    metrics_collection_epochs: Incomplete
    collect_metrics_on_train_end: Incomplete
    collect_val_only: Incomplete
    batch_size: Incomplete
    pipeline_params: Incomplete
    collect_predictions: Incomplete
    collect_embeddings: Incomplete
    embeddings_dim: Incomplete
    embeddings_method: Incomplete
    inference_chunk_size: Incomplete
    dataloader_args: Incomplete
    def __init__(self, project_name: str | None = None, run_name: str | None = None, run_description: str | None = None, image_column_name: str = 'image', label_column_name: str | None = None, metrics_collection_epochs: list[int] | None = None, collect_metrics_on_train_end: bool = True, collect_val_only: bool = False, batch_size: int | None = 32, pipeline_params: PipelineParams | dict[str, Any] | None = None, collect_predictions: bool | None = None, collect_embeddings: bool = False, embeddings_dim: int = 2, embeddings_method: Literal['pacmap', 'umap'] = 'pacmap', inference_chunk_size: int | None = None, dataloader_args: dict[str, Any] | None = None) -> None:
        """Create a new metrics collection callback.

        :param project_name: The name of the 3LC project to use if no active run exists.
        :param run_name: The name of the 3LC run to use if no active run exists.
        :param run_description: The description of the 3LC run to use if no active run exists.
        :param image_column_name: The name of the column in the table that contains the images.
        :param label_column_name: The name of the column in the table that contains the labels. If not provided, a
            task-specific default will be used.
        :param metrics_collection_epochs: The zero-indexed epochs after which to collect metrics.
        :param collect_metrics_on_train_end: Whether to collect metrics after training finishes.
        :param collect_val_only: Whether to collect metrics only on the validation set.
        :param metrics_collection_dataloader_args: Additional arguments to pass to the dataloaders used for metrics
            collection.
        :param batch_size: The batch size to use for metrics collection, passed to the SuperGradients `Pipeline`s when
            performing inference. Controls the number of images in each batch on the device.
        :param pipeline_params: The pipeline parameters to use for metrics collection. Can be provided as a
            PipelineParams instance, a dictionary, or None (default) which will use a default PipelineParams instance.
        :param collect_predictions: Whether to collect predictions. Default is None, which means predictions will be
            logged for all task-specific subclasses if not explicitly set to False. On using the base callback, no
            predictions will be logged by default.
        :param collect_embeddings: Whether to collect embeddings. Is only applied if the model has a backbone attribute
            (Yolo-NAS models have this). Default is False because embeddings collection performs additional inference
            and therefore spends additional time.
        :param embeddings_dim: The dimensionality to reduce the embeddings to, default is 2. 2 or 3 are recommended.
        :param embeddings_method: The method to use for reducing the embeddings.
        :param inference_chunk_size: How many images to load into CPU memory at once for each dataloader worker batch.
            The number of (full-size) images in CPU memory at a time is batch_size * inference_chunk_size. If not
            provided, batch_size is used if not set to None, else 32 is used.
        :param dataloader_args: Additional arguments to pass to the dataloader used for metrics collection. By default,
            8 workers and no pinning of memory is used. batch_size is set to the value of the parameter
            inference_chunk_size, any value provided here is ignored. If inference_chunk_size is not provided,
            batch_size is used. Shuffling is disallowed.
        """
    @property
    def run(self) -> Run: ...
    @multi_process_safe
    def on_training_start(self, context: PhaseContext) -> None:
        """Called when training starts, creates a 3LC run if no active run exists and logs hyperparameters.

        :raises ValueError: If project_name or run_name is provided and different from those of an existing active run.
        """
    @multi_process_safe
    def on_train_loader_end(self, context: PhaseContext) -> None:
        """Called when the training loader ends, logs aggregate SuperGradients metrics to the 3LC run."""
    @multi_process_safe
    def on_validation_loader_end(self, context: PhaseContext) -> None:
        """Called when the validation loader ends, logs aggregate SuperGradients metrics to the 3LC run."""
    @multi_process_safe
    def on_training_end(self, context: PhaseContext) -> None:
        """Called when training ends, invokes metrics collection if configured to and updates the run status.

        :param context: The PhaseContext received from the SuperGradients Trainer.
        """
    def collect_metrics_direct(self, model: SgModule, tables: list[Table], constants: dict[str, Any] | None = None) -> None:
        """Collect metrics directly on tables.

        :param model: The model to collect metrics from.
        :param tables: The tables to collect metrics from.
        :param constants: Additional constants to pass to the metrics collection.
        """
    def compute_metrics(self, images: list[str], predictions: ImagesPredictions | ImagePrediction, table: Table) -> dict[str, Any]:
        """Compute metrics for a batch of images and corresponding predictions.

        :param images: A list of absolute image URLs as strings.
        :param predictions: A list of predictions or a single prediction.
        :param table: The table containing the images and predictions.
        :returns: A dictionary of computed metrics.
        """
    def metrics_column_schemas(self, table: Table) -> dict[str, Schema]:
        """Return the column schemas for the metrics of this callback."""
    @property
    def label_column_name(self) -> str:
        """The name of the label column."""

class _InferenceDataset(Dataset):
    table: Incomplete
    images: Incomplete
    def __init__(self, table: Table, image_column_name: str) -> None: ...
    def __len__(self) -> int: ...
    def __getitem__(self, idx: int) -> torch.Tensor: ...
