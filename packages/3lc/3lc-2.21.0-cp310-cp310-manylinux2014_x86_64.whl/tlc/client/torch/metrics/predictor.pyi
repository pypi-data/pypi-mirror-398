import torch
from _typeshed import Incomplete
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from tlc.core.builtins.types import SampleData as SampleData
from tlc.core.type_helper import TypeHelper as TypeHelper
from torch.utils.hooks import RemovableHandle as RemovableHandle
from types import TracebackType
from typing import Any, Callable

logger: Incomplete

class _ModelModeGuard:
    """A context manager to temporarily switch a model to evaluation mode."""
    model: Incomplete
    was_training: Incomplete
    def __init__(self, model: torch.nn.Module) -> None: ...
    def __enter__(self) -> None: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType | None) -> None: ...

@dataclass
class PredictorArgs:
    """Arguments for the Predictor class."""
    layers: Sequence[int] = field(default_factory=list)
    unpack_dicts: bool = field(default=False)
    unpack_lists: bool = field(default=False)
    preprocess_fn: Callable[[SampleData], Any] | None = field(default=None)
    disable_preprocess: bool = field(default=False)
    device: torch.device | str | None = field(default=None)
    call_fn: str | None = field(default=None)

@dataclass
class PredictorOutput:
    """The output of the Predictor class."""
    forward: Any = field(default=None)
    hidden_layers: dict[int, torch.Tensor] | None = field(default=None)
    metadata: dict[str, Any] | None = field(default=None)

class Predictor:
    """A wrapper for PyTorch models that handles preprocessing, device management, embedding extraction, and prediction.

    A high-level wrapper around a PyTorch model designed to standardize the workflow of processing inputs, making
    predictions, and handling outputs. It serves to unify the interface for different PyTorch models, ensuring
    consistency and ease of use across various modeling tasks.

    A Predictor can be configured to extract hidden layer activations from the model during a forward pass by supplying
    the {attr}`PredictorArgs.layers` argument to the constructor. These activations are stored in the
    {class}`PredictorOutput`, and can be used for downstream tasks such as feature extraction, visualization, or
    debugging.

    See the [](inv:pytorch#torch.nn.Module) documentation for more information on PyTorch models and modules.
    """
    args: Incomplete
    model: Incomplete
    device: Incomplete
    def __init__(self, model: torch.nn.Module, **predictor_args: Any) -> None:
        """Initializes the Predictor with a model and optional arguments.

        :param model: A torch.nn.Module model for which predictions will be made.
        :param **predictor_args: Arbitrary keyword arguments that will be passed to the
            {class}`PredictorArgs<PredictorArgs>` dataclass. These can include configurations such as which layers to
            hook for output, preprocessing functions, device specifications, and whether to unpack dictionaries or lists
            when passing data to the model.
        """
    def get_device(self) -> torch.device:
        """Determines the appropriate device for model computation.

        If a device is specified in the predictor arguments, it is used. Otherwise, attempts to use the same device as
        the model parameters. Defaults to CPU if the model has no parameters.
        """
    def preprocess(self, batch: SampleData) -> SampleData:
        """Applies preprocessing to the input batch, based on the predictor arguments.

        If a custom preprocessing function is provided, it is used. Otherwise, default preprocessing is applied.

        The default preprocessing behavior attempts to identify the input data within the batch using the following
        heuristics:

        - If the batch is a list of dictionaries, it is assumed that the input data is already preprocessed.
        - If the batch is a tuple or list, the first item is assumed to be the input data.
        - If the batch is a dictionary, the input data is assumed to be under the keys `image`, `images`,
          or `pixel_values`.

        To disable preprocessing, set the disable_preprocess argument to True.

        :param batch: The input data batch to preprocess.
        :returns: The preprocessed data batch.
        """
    def to_device(self, batch: SampleData) -> SampleData:
        """Moves the batch of data to the appropriate device.

        This method uses a utility function to recursively move all tensors
        in the batch to the specified device.

        :param batch: The preprocessed data batch to move to the device.
        :returns: The data batch, with all tensors moved to the specified device.
        """
    def __call__(self, batch: SampleData) -> PredictorOutput:
        """Processes a batch of inputs and passes them through the model.

        The batch is preprocessed, moved to the appropriate device, and then passed to the model. Outputs from the model
        and any hooked layers are packaged into a PredictorOutput.

        :param batch: The input data batch to process.
        :returns PredictorOutput: The model's predictions and any collected hidden layer outputs.
        """
    def call_model(self, processed_batch: SampleData) -> SampleData:
        """Calls the model with the processed batch, handling unpacking if necessary.

        This method supports passing the batch to the model as unpacked dictionaries
        or lists, based on the predictor arguments, or directly if no unpacking is required.

        :param processed_batch: The batch of data to pass to the model, already preprocessed.
        :returns: The raw forward pass output from the model.
        """
    @contextmanager
    def with_hooks(self) -> Generator[None, None, None]:
        """A context manager to temporarily add forward hooks during a block of code.

        This context manager ensures that forward hooks are added before entering the block and removed after exiting.
        """
    def __del__(self) -> None:
        """Remove forward hooks upon deletion of the Predictor instance."""
