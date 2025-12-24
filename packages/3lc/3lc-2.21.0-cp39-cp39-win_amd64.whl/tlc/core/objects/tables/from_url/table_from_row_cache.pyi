from _typeshed import Incomplete
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.tables.from_url.table_from_parquet import TableFromParquet as TableFromParquet
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class TableFromRowCache(TableFromParquet):
    """A table that wraps another table based on its row cache.

    A `TableFromRowCache` enables a limited representation of unknown Table types that are not registered in the system.
    Note that the UnknownTable's derived properties are not initialized and are only present as plain objects.

    The `TableFromRowCache` is not intended for direct instantiation, use the `TableFromParquet` whenever explicit
    loading of tables from parquet files is desired. Instead, the `TableFromRowCache` should be used as a utility for
    loading and representing tables that are not registered in the system. It offers an abstracted interface to work
    with these unknown table types while maintaining system integrity.

    The implementation is a minimal wrapper around [TableFromParquet](TableFromParquet).

    This `TableFromRowCache` can be used to represent other Table types as long as the following requirements are met:
      - The object must have a row_cache_url set
      - The object must have row_cache_populated set
      - The object must have a schema set

    Limitations:
      - Initialization: `TableFromRowCache` can only be initialized using the `init_params` as is done when calling
          [Table.from_url](Table.from_url) or
          [ObjectRegistry.get_or_create_object_from_url](ObjectRegistry.get_or_create_object_from_url). Direct
          initialization is not supported. Use `TableFromParquet` instead.
      - Write Restriction: The table cannot be written to a URL since it would mean overwriting the original table
           and losing information therein. Again, use `TableFromParquet` if a persistent table is desired.
      - Plain attributes: Derived attributes are not initialized and are plain objects, for example: `input_url`s are
        strings and not Url objects.

    :param init_parameters: The parameters to initialize the object with.
    """
    type: Incomplete
    row_cache_url: Incomplete
    input_url: Incomplete
    row_cache_populated: Incomplete
    absolute_input_url: Incomplete
    def __init__(self, init_parameters: Any, url: Url | None = None) -> None: ...
    @staticmethod
    def can_create_from_content(parameters: Any) -> type[Object] | None:
        """Determines whether a `TableFromRowCache` can be created from the given parameters.

        This can be used to determine whether a serialized Table of another type can be represented as a
        `TableFromRowCache`. The following is required:
        - The table must have a row_cache_url set
        - The table must have a row_cache_populated set
        - The table must have a schema set

        :param parameters: The parameters to check.
        :return: The type of the object that can be created from the given parameters, or None if no object can be
            created.
        """
    def write_to_url(self, force: bool = False) -> Url: ...
