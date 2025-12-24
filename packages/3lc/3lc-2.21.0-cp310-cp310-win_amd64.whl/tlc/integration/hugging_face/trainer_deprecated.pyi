import transformers
from _typeshed import Incomplete
from tlc.client.helpers import active_run as active_run
from tlc.client.session import Session as Session
from tlc.core.builtins.types import MetricData as MetricData
from tlc.core.exceptions import TLCException as TLCException
from tlc.core.objects.table import Table as Table
from tlc.core.writers import MetricsTableWriter as MetricsTableWriter
from torch import Tensor, nn as nn
from torch.utils.data import Dataset as Dataset
from transformers import EvalPrediction as EvalPrediction, IntervalStrategy as IntervalStrategy
from typing import Any, Callable

msg: str
logger: Incomplete

class TLCTrainer(transformers.Trainer):
    '''A drop-in replacement for the 🤗 transformers Trainer.

    Adds per-sample metrics collection on both the train and eval datasets every time .evaluate() is called.

    To specify what metrics to collect, pass in a function to the compute_tlc_metrics argument that takes in a batch
    of data and returns a dictionary of per-sample metrics for the batch.

    :param compute_hf_metrics: The function that will be used to compute metrics at evaluation. Must take a
        [`EvalPrediction`] and return a dictionary string to metric values. Also called compute_metrics in HF Trainer.
    :param compute_tlc_metrics: A function that takes in a batch of data and returns a dictionary of metrics.
    :param compute_tlc_metrics_on_train_begin: Whether to collect metrics before training starts.
    :param compute_tlc_metrics_on_train_end: Whether to collect metrics after training ends.
    :param tlc_metrics_collection_start: The iteration or epoch to start collecting metrics on. Can be use with
        eval_strategy as "epochs" or "steps". If eval_strategy is "steps", tlc_metrics_collection_start needs
        to be a multiple of eval_steps.
    :param tlc_metrics_collection_epoch_frequency: The epoch frequency with which to collect metrics. Must be greater
        than 0 for metrics to be collected during training. Please use eval_steps for "steps" evaluation strategy.
    '''
    compute_tlc_metrics: Incomplete
    compute_tlc_metrics_on_train_begin: Incomplete
    compute_tlc_metrics_on_train_end: Incomplete
    tlc_metrics_collection_start: Incomplete
    tlc_metrics_collection_epoch_frequency: Incomplete
    def __init__(self, *args: Any, compute_hf_metrics: Callable[[EvalPrediction], dict] | None = None, compute_tlc_metrics: Callable[[Tensor | None, Tensor | None], dict[str, MetricData]] | None = None, compute_tlc_metrics_on_train_begin: bool = False, compute_tlc_metrics_on_train_end: bool = False, tlc_metrics_collection_start: int = 0, tlc_metrics_collection_epoch_frequency: int = -1, **kwargs: Any) -> None: ...
    def get_current_epoch(self) -> int: ...
    def get_current_global_step(self) -> int: ...
    def train(self, *args: Any, **kwargs: Any) -> Any:
        """
        Overriding original `train` method to register start the compute_metrics process when needed.

        Args:
            args (`dict[str, Any]`):
                Arguments to pass to the original `train` method.
            kwargs (`dict[str, Any]`, *optional*):
                Additional keyword arguments to pass to the original `train` method.
        """
    def prediction_step(self, model: nn.Module, inputs: dict[str, Tensor | Any], prediction_loss_only: bool, ignore_keys: list[str] | None = None) -> tuple[Tensor | None, Tensor | None, Tensor | None]:
        """
        Overriding original `prediction_step method` to compute metrics with 3LC.

        Backward compatibility with the original `prediction_step` method is maintained if `compute_tlc_metrics` is not
        set or the specific frequency is not hit.

        Args:
            model (`nn.Module`):
                The model to evaluate.
            inputs (`dict[str, Union[torch.Tensor, Any]]`):
                The inputs and targets of the model.

                The dictionary will be unpacked before being fed to the model. Most models expect the targets under the
                argument `labels`. Check your model's documentation for all accepted arguments.
            prediction_loss_only (`bool`):
                Whether or not to return the loss only.
            ignore_keys (`list[str]`, *optional*):
                A list of keys in the output of your model (if it is a dictionary) that should be ignored when
                gathering predictions.

        Returns:
            tuple[Optional[torch.Tensor], Optional[torch.Tensor], Optional[torch.Tensor]]: A tuple with the loss,
            logits and labels (each being optional).
        """
    def collect_metrics_with_tlc(self, ignore_keys: list[str] | None = None, metric_key_prefix: str = 'eval') -> dict[str, float]:
        '''
        Method used to run evaluation on both training  and evaluation datasets with tlc metrics collection.

        Args:
            ignore_keys (`list[str]`, *optional*):
                A list of keys in the output of your model (if it is a dictionary) that should be ignored when
                gathering predictions.
            metric_key_prefix (`str`, *optional*, defaults to `"eval"`):
                An optional prefix to be used as the metrics key prefix. For example the metrics "bleu" will be named
                "eval_bleu" if the prefix is "eval" (default)

        Returns:
            A dictionary containing the evaluation loss and the potential metrics computed from the predictions. The
            dictionary also contains the epoch number which comes from the training state.
        '''
    def run_default_evaluate_based_on_eval_strategy(self, eval_strategy: IntervalStrategy | str) -> bool:
        """
        Method to know when we should apply the default evaluation behavior of the Trainer or using 3LC evaluation.

        Args:
            eval_strategy (`IntervalStrategy` or `str`):
                The evaluation strategy to check if the current frequency
                is hit

        Returns:
            A boolean indicating if the default evaluation behavior should be applied or not.
        """
    def evaluate(self, eval_dataset: Dataset | None = None, ignore_keys: list[str] | None = None, metric_key_prefix: str = 'eval', force_collect_metrics: bool = False) -> dict[str, float]:
        '''
        Overloading method to collect metrics with or without 3LC.

        Backward compatibility with the original `evaluate` method is maintained if `compute_tlc_metrics` is not set or
        the specific frequency is not hit.

        Args:
            eval_dataset (`Dataset`, *optional*):
                Pass a dataset if you wish to override `self.eval_dataset`. If it is a [`~datasets.Dataset`], columns
                not accepted by the `model.forward()` method are automatically removed. It must implement the `__len__`
                method.
            ignore_keys (`list[str]`, *optional*):
                A list of keys in the output of your model (if it is a dictionary) that should be ignored when
                gathering predictions.
            metric_key_prefix (`str`, *optional*, defaults to `"eval"`):
                An optional prefix to be used as the metrics key prefix. For example the metrics "bleu" will be named
                "eval_bleu" if the prefix is "eval" (default)
            force_collect_metrics (`bool`, *optional*, defaults to `False`):
                An optional flag to force the collection of metrics even if the evaluation strategy does not require it.
                Used specifically to force collecting metrics on train begin or on train end.

        Returns:
            A dictionary containing the evaluation loss and the potential metrics computed from the predictions. The
            dictionary also contains the epoch number which comes from the training state.
        '''
