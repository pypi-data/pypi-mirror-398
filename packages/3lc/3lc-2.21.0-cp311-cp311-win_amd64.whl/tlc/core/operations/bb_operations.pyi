import torch
from PIL import Image
from _typeshed import Incomplete
from collections.abc import Mapping
from pathlib import Path
from tlc.core.builtins.constants.column_names import BOUNDING_BOXES as BOUNDING_BOXES, BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH, PREDICTED_BOUNDING_BOXES as PREDICTED_BOUNDING_BOXES
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_NN_EMBEDDING as NUMBER_ROLE_NN_EMBEDDING
from tlc.core.builtins.constants.string_roles import STRING_ROLE_IMAGE_URL as STRING_ROLE_IMAGE_URL
from tlc.core.builtins.types.bb_crop_interface import BBCropInterface as BBCropInterface
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.operations.operation import CalculateSchemaContext as CalculateSchemaContext, CalculateValueContext as CalculateValueContext, GlobalOperation as GlobalOperation, LocalOperation as LocalOperation
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from typing import Any, Callable

class BBCropMixin:
    """Mixin for operations that use BBCropInterface.

    Provides helper-functionality and re-use of written crop images between operations.
    """
    @staticmethod
    def get_image_url_columns(input_schemas: dict[str, Schema]) -> list[str]: ...
    @staticmethod
    def get_bb_columns(input_schemas: dict[str, Schema]) -> list[str]: ...
    @staticmethod
    def create_crop_url(input_table_url: Url, row_idx: int | str = '[row_idx]') -> Path:
        """Creates a deterministic URL for a crop image."""

class BBCropEmbeddingOperation(GlobalOperation, BBCropMixin):
    """Operation that uses BBCropInterface to crop images and then embeds them using a neural network.

    The embedder network can be provided as an argument, or a default ResNet18 model will be used.

    :param embeddings_model: The neural network to use for embedding. If None, a default ResNet18 model will be used.
    :param embeddings_dim: The dimensionality of the embeddings produced by the neural network.
    :param transforms: A callable that transforms a PIL image into a tensor.
    :param batch_size: The batch size to use when embedding images.
    :param num_workers: The number of workers to use when embedding images.
    """
    device: Incomplete
    model: Incomplete
    embeddings_dim: Incomplete
    transforms: Incomplete
    batch_size: Incomplete
    num_workers: Incomplete
    def __init__(self, embeddings_model: torch.nn.Module | None = None, embeddings_dim: int = 512, transforms: Callable[[Image.Image], torch.Tensor] | None = None, batch_size: int = 16, num_workers: int = 0) -> None: ...
    def populate_column_data(self, calculate_value_context: CalculateValueContext) -> list[Any]: ...
    def calculate_schema(self, calculate_schema_context: CalculateSchemaContext) -> Schema: ...

class BBCropRGBAverageOperation(LocalOperation, BBCropMixin):
    '''Operation that uses BBCropInterface to crop images and then calculates the average RGB value of the crop.

    The average RGB values are returned as a dictionary with keys "red_avg", "green_avg", and "blue_avg".
    '''
    def calculate_schema(self, calculate_schema_context: CalculateSchemaContext) -> Schema: ...
    def calculate_single_value(self, row: Mapping[str, Any], calculate_value_context: CalculateValueContext) -> Any: ...

class BBCropOperation(LocalOperation, BBCropMixin):
    """Operation that uses BBCropInterface to crop images and then returns the cropped image.

    Filenames for image crops are deterministic based on the input table and row index.
    If the image already exists, it will be loaded from disk instead of being re-cropped.
    """
    def calculate_schema(self, calculate_schema_context: CalculateSchemaContext) -> Schema: ...
    def calculate_single_value(self, row: Mapping[str, Any], calculate_value_context: CalculateValueContext) -> Any: ...
