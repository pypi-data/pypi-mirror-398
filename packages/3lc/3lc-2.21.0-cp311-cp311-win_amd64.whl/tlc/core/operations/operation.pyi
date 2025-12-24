import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from collections.abc import Mapping
from tlc.core.objects.table import Table as Table
from tlc.core.schema import Schema as Schema
from tlc.core.utils.progress import track as track
from typing import Any

class CalculateValueContext:
    """Represents the context in which a value is calculated."""
    input_column_data: list[Any]
    input_table_row: int
    input_table_schemas: Incomplete
    output_property_schema: Any
    property_internal_name: list[str]
    table: Incomplete
    table_row: int
    column_setup: Any
    def __init__(self, table: Table, input_table_schemas: dict[str, Schema]) -> None: ...

class CalculateSchemaContext:
    """Represents the context in which a schema is calculated."""
    input_table_row_schemas: Incomplete
    def __init__(self, input_table_row_schemas: dict[str, Schema]) -> None: ...

class Operation(ABC, metaclass=abc.ABCMeta):
    """An abstract base class representing a generic operation on data.

    Subclasses must implement the `calculate_schema` as well as either `populate_column_data` for global operations or
    `calculate_single_value` for local operations.
    """
    @abstractmethod
    def calculate_schema(self, calculate_schema_context: CalculateSchemaContext) -> Schema:
        """Calculate the schema for the resulting table based on input schemas."""
    @abstractmethod
    def populate_column_data(self, calculate_value_context: CalculateValueContext) -> list[Any]:
        """Populate column data based on the operation and input table."""
    def column_name(self) -> str:
        """Generate a unique column name based on the object id."""

class LocalOperation(Operation, metaclass=abc.ABCMeta):
    """An abstract base class representing a local operation on data.

    Subclasses must implement the `calculate_single_value` method.
    """
    @abstractmethod
    def calculate_single_value(self, row: Mapping[str, object], calculate_value_context: CalculateValueContext) -> object:
        """Calculate a single value for a row based on the operation."""
    def populate_column_data(self, calculate_value_context: CalculateValueContext) -> list[object]:
        """Populate a list of values for a new column in the table."""

class GlobalOperation(Operation, metaclass=abc.ABCMeta):
    """An abstract base class representing a global operation on data.

    Acts on entire columns of data.
    """
