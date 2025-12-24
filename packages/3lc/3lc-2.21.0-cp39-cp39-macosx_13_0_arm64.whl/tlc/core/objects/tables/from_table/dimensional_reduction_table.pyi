import abc
import numpy as np
from _typeshed import Incomplete
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_XYZ_COMPONENT as NUMBER_ROLE_XYZ_COMPONENT, NUMBER_ROLE_XY_COMPONENT as NUMBER_ROLE_XY_COMPONENT
from tlc.core.builtins.constants.string_roles import STRING_ROLE_URL as STRING_ROLE_URL
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.objects.table import ImmutableDict as ImmutableDict, Table as Table, TableRow as TableRow
from tlc.core.objects.tables.from_table.schema_helper import input_table_schema as input_table_schema
from tlc.core.objects.tables.in_memory_columns_table import _InMemoryColumnsTable
from tlc.core.schema import BoolValue as BoolValue, DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Int32Value as Int32Value, Schema as Schema, StringValue as StringValue
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from typing import Any, Protocol

logger: Incomplete

class _ReducerProtocol(Protocol):
    def transform(self, data: np.ndarray) -> np.ndarray: ...

class _DimensionalReductionTable(_InMemoryColumnsTable, metaclass=abc.ABCMeta):
    """A base class for tables performing dimensionality reduction."""
    algorithm_name: str
    input_table_url: ObjectReference
    source_embedding_column: str
    target_embedding_column: str
    retain_source_embedding_column: bool
    standard_scaler_normalize: bool
    n_components: int
    fit_table_url: ObjectReference | None
    random_state: int | None
    model_url: Url
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, input_table_url: Url | Table | None = None, source_embedding_column: str | None = None, target_embedding_column: str | None = None, retain_source_embedding_column: bool | None = None, standard_scaler_normalize: bool | None = None, fit_table_url: Table | Url | None = None, model_url: Url | None = None, n_components: int | None = None, random_state: int | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None:
        """Creates a derived table with a new column containing the dimensionally reduced data.

        :param input_table_url: The input table to apply the dimensionality reduction to
        :param source_embedding_column: The column in the input table to apply dimensionality reduction to
        :param target_embedding_column: The name of the new column to create in the output table
        :param retain_source_embedding_column: Whether to retain the source column in the input table, defaults to False
        :param standard_scaler_normalize: Whether to apply the sklearn standard scaler to input before reducing,
            defaults to False
        :param fit_table_url: The table to use for fitting reduction transform.
            If not specified, the input table is used.
        :param model_url: The URL to store/load the reducer model file. If empty, no model is saved.
        :param n_components: The dimension of the output embedding
        :param random_state: The random seed for the reducer algorithm
        """
