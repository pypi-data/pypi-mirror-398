from _typeshed import Incomplete
from tlc.client.bulk_data_url_utils import bulk_data_url_context as bulk_data_url_context
from tlc.client.sample_type import Box as Box, CompositeSampleType as CompositeSampleType, SampleType as SampleType
from tlc.client.utils import standardized_transforms as standardized_transforms, without_transforms as without_transforms
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.tables.in_memory_rows_table import _InMemoryRowsTable
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from tlc.utils.decorators import disallow_positional_arguments as disallow_positional_arguments
from torch.utils.data import Dataset as Dataset
from typing import Any

logger: Incomplete

class TableFromTorchDataset(_InMemoryRowsTable):
    """A table populated from a Torch dataset.

    When creating a `TableFromTorchDataset`, the row schema specified by the `override_table_rows_schema` parameter (if
    provided) must match the structure of the samples in the provided `input_dataset`. This row schema is used to
    convert the samples in the `input_dataset` to rows in the table, and to make sure that samples returned by the
    table's `__getitem__` method match the structure of the samples in the original `input_dataset`.

    If the `input_dataset` is a `torchvision.datasets.DatasetFolder`, the `TableFromTorchDataset` will use the
    `torchvision.datasets.folder.default_loader` to load the images. This loader will be replaced with a 3LC loader
    that does not copy the images, but instead returns a PIL image with a filename attribute that contains the
    absolute path to the image. This allows the front-end to access the images in the table without copying them.

    If the `input_dataset` is a `torchvision.datasets.VisionDataset`, the `TableFromTorchDataset` will also remove
    any transforms from the `input_dataset` before serializing it to the table, but will recreate the transforms
    on the `VisionDataset` after serialization. Any transforms defined on the `input_dataset` are added to the list
    of `map_functions` of the `Table`, and will be reflected in the samples returned by the `Table`'s `__getitem__`
    method, but not serialized to the `Table`'s json file.
    """
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Schema | None = None, init_parameters: Any | None = None, input_dataset: Dataset | None = None, all_arrays_are_fixed_size: bool = False, input_tables: list[Url] | None = None) -> None:
        """Create a Table from a Torch dataset.

        :param url: The URL of the table.
        :param created: The date and time the table was created.
        :param description: A description of the table.
        :param dataset_name: The name of the dataset.
        :param project_name: The name of the project.
        :param row_cache_url: The URL of the row cache.
        :param row_cache_populated: Whether the row cache has been populated.
        :param override_table_rows_schema: The schema of the table rows.
        :param init_parameters: The parameters used to initialize the table.
        :param input_dataset: The Torch dataset to use to populate the table.
        """
