import torch
from _typeshed import Incomplete
from tlc.client.helpers import active_run as active_run
from tlc.client.session import init as init
from tlc.client.torch.metrics.collect import collect_metrics as collect_metrics
from tlc.client.torch.metrics.metrics_collectors.metrics_collector_base import MetricsCollectorType as MetricsCollectorType
from tlc.client.torch.metrics.predictor import Predictor as Predictor
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.objects.table import Table as Table
from tlc.core.url import Url as Url
from tlc.integration.hugging_face.trainer_deprecated import TLCTrainer as TLCTrainer
from torch import nn as nn
from transformers import BaseImageProcessor as BaseImageProcessor, EvalPrediction as EvalPrediction, FeatureExtractionMixin as FeatureExtractionMixin, PreTrainedModel as PreTrainedModel, PreTrainedTokenizerBase as PreTrainedTokenizerBase, ProcessorMixin as ProcessorMixin, Trainer as HF_Trainer, TrainerCallback, TrainerControl as TrainerControl, TrainerState as TrainerState, TrainingArguments as TrainingArguments
from typing import Any, Callable

logger: Incomplete

class _MetricsCollectionCallback(TrainerCallback):
    def __init__(self, metrics_collection_epochs: set[int], metrics_collectors: MetricsCollectorType, run_url: Url, exclude_zero_weights_metrics_collection: bool, data_collator: Callable | None) -> None: ...
    def on_train_begin(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, model: PreTrainedModel | nn.Module, train_dataloader: torch.utils.data.DataLoader | None = None, eval_dataloader: torch.utils.data.DataLoader | None = None, **kwargs: Any) -> None: ...
    def on_epoch_end(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, model: PreTrainedModel | nn.Module, train_dataloader: torch.utils.data.DataLoader | None = None, eval_dataloader: torch.utils.data.DataLoader | None = None, **kwargs: Any) -> None: ...
    def on_train_end(self, args: TrainingArguments, state: TrainerState, control: TrainerControl, **kwargs: Any) -> None: ...

class Trainer(HF_Trainer):
    train_dataset: Table | None
    eval_dataset: Table | dict[str, Table] | None
    def __init__(self, model: PreTrainedModel | nn.Module | None = None, args: TrainingArguments | None = None, data_collator: Callable | None = None, train_dataset: Table | None = None, eval_dataset: Table | dict[str, Table] | None = None, processing_class: PreTrainedTokenizerBase | BaseImageProcessor | FeatureExtractionMixin | ProcessorMixin | None = None, model_init: Callable[[], PreTrainedModel] | None = None, compute_loss_func: Callable | None = None, compute_metrics: Callable[[EvalPrediction], dict] | None = None, callbacks: list[TrainerCallback] | None = None, optimizers: tuple[torch.optim.Optimizer | None, torch.optim.lr_scheduler.LambdaLR | None] = (None, None), preprocess_logits_for_metrics: Callable[[torch.Tensor, torch.Tensor], torch.Tensor] | None = None, *, run_name: str | None = None, run_description: str | None = None, exclude_zero_weights_metrics_collection: bool = False, exclude_zero_weights_train: bool = True, weighted: bool = True, shuffle: bool = True, repeat_by_weight: bool = False, metrics_collectors: MetricsCollectorType | None = None, metrics_collection_epochs: list[int] | None = None) -> None: ...
