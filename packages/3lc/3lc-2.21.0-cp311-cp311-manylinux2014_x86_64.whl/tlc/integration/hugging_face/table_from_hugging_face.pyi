import datasets
from _typeshed import Incomplete
from tlc.client.bulk_data_url_utils import bulk_data_url_context as bulk_data_url_context
from tlc.client.sample_type import SampleType as SampleType
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.tables.in_memory_rows_table import _InMemoryRowsTable
from tlc.core.schema import Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from typing import Any

msg: str

class TableFromHuggingFace(_InMemoryRowsTable):
    '''A Table object for representing a Hugging Face dataset.

    The `TableFromHuggingFace` class is an interface between 3LC and the Hugging Face datasets library. For datasets
    with multiple subsets, use `hugging_face_name` to specify the subset. Use `hugging_face_split` to specify the
    desired split.

    :Example:
    ```python
    table = TableFromHuggingFace(
        hugging_face_path="glue",
        hugging_face_name="mrpc",
        hugging_face_split="train",
    )
    print(table.table_rows[0])
    ```

    :param hugging_face_path: The path to the Hugging Face dataset.
    :param hugging_face_name: Name or configuration of the subset. Optional.
    :param hugging_face_split: The split to use. Optional, defaults to train.
    :returns: An instance of the `TableFromHuggingFace` class.
    :raises: `ValueError` if the Hugging Face dataset is not provided.
    '''
    hugging_face_path: Incomplete
    hugging_face_name: Incomplete
    hugging_face_split: Incomplete
    def __init__(self, hugging_face_path: str | None = None, hugging_face_name: str | None = None, hugging_face_split: str | None = None, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, override_table_rows_schema: Any = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None: ...
    @property
    def hf_dataset(self) -> datasets.Dataset: ...
    @property
    def sample_type(self) -> SampleType: ...
