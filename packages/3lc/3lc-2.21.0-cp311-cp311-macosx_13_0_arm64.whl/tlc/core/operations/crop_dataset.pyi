import torch
from PIL import Image
from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import BOUNDING_BOX_LIST as BOUNDING_BOX_LIST, IMAGE_HEIGHT as IMAGE_HEIGHT, IMAGE_WIDTH as IMAGE_WIDTH
from tlc.core.builtins.types.bb_crop_interface import BBCropInterface as BBCropInterface
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from torch.utils.data import Dataset
from typing import Any, Callable

class _SquarePad:
    """Zero-pads image on the sides to make it square."""
    def __call__(self, image: Image.Image) -> Image.Image: ...

class _ImageCropDataset(Dataset):
    table: Incomplete
    transforms: Incomplete
    bb_schema: Incomplete
    image_column: Incomplete
    bb_column: Incomplete
    crop_root_url: Incomplete
    def __init__(self, table: Table, transforms: Callable[[Image.Image], torch.Tensor] | None, bb_schema: Schema, image_column: str, bb_column: str, crop_root_url: str) -> None: ...
    def __len__(self) -> int: ...
    def __getitem__(self, idx: int) -> Any: ...
