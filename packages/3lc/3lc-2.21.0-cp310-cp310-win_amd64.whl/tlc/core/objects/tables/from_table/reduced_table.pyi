import abc
from _typeshed import Incomplete
from abc import abstractmethod
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_FOREIGN_KEY as NUMBER_ROLE_FOREIGN_KEY
from tlc.core.object_reference import ObjectReference as ObjectReference
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.objects.tables.from_table.schema_helper import input_table_schema as input_table_schema
from tlc.core.objects.tables.in_memory_rows_table import _InMemoryRowsTable
from tlc.core.schema import BoolValue as BoolValue, DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Float64Value as Float64Value, Int16Value as Int16Value, Int32Value as Int32Value, Int64Value as Int64Value, Int8Value as Int8Value, MapElement as MapElement, NumericValue as NumericValue, ScalarValue as ScalarValue, Schema as Schema, StringValue as StringValue, Uint16Value as Uint16Value, Uint32Value as Uint32Value, Uint64Value as Uint64Value, Uint8Value as Uint8Value
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class _ReducerBase(metaclass=abc.ABCMeta):
    @abstractmethod
    def __call__(self, a: Any) -> Any: ...
    @abstractmethod
    def value(self) -> Any: ...

class _RowReducer(_ReducerBase):
    def __init__(self, row_schema: Schema, omit_properties: dict[str, Any]) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    def value(self) -> dict[str, Any]: ...

class _ColumnReducer(_ReducerBase):
    def __init__(self, col_schema: Schema) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    def value(self) -> Any: ...

class _SumReducer(_ReducerBase):
    def __init__(self, schema: ScalarValue) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    @property
    def sum(self) -> Any: ...
    def value(self) -> Any: ...

class _AverageReducer(_SumReducer):
    """A class for handling reduction of numeric scalar values"""
    def __init__(self, schema: ScalarValue) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    @property
    def count(self) -> Any: ...
    @property
    def avg(self) -> Any: ...
    def value(self) -> Any: ...

class _StringReducer(_ReducerBase):
    """A class for handling reduction of string values

    String reduction is simple, either the input is:
       * constant => reduction == constant,
       * not constant => reduction == the literal 'multiple_values'

    """
    def __init__(self, schema: ScalarValue) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    def value(self) -> Any: ...

class _ArrayReducer(_AverageReducer):
    """A class for handling reduction of array values

    Array reduction just wraps the call to the numeric reducer in a numpy array, otherwise its the same as
    NumericAverageReducer

    If the input is a tuple, the output is a tuple, otherwise the output is a list.
    """
    is_tuple: bool
    def __init__(self, schema: ScalarValue) -> None: ...
    def __call__(self, a: Any) -> Any: ...
    def value(self) -> Any: ...

class ReducedTable(_InMemoryRowsTable):
    '''
    A procedural table where an input table has been reduced on one or more properties.

    The reduction is performed by grouping all rows that have the same set of values, eg example_id, and then performing
    a reduction on each group. Currently the only reduction supported is average (mean) with some special handling for
    string and boolean value types.

    Example:
    ```python
    from tlc.core import *

    # create a table with two columns, example_id and value
    table = TableFromPydict(data={"example_id": [1, 1, 2, 2], "value": [1, 2, 3, 4]})
    # reduce the table by example_id, averaging the value column
    reduced_table = ReducedTable(input_table_url=table, reduce_properties=["example_id"])
    for row in reduced_table.table_rows:
        print(row)
    # prints:
    # {\'example_id\': 1, \'value\': 1.5}
    # {\'example_id\': 2, \'value\': 3.5}
    ```

    '''
    reduce_properties: list[str]
    input_table_url: Incomplete
    def __init__(self, *, url: Url | None = None, created: str | None = None, description: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, reduce_properties: list[str] | None = None, input_table_url: Url | Table | None = None, init_parameters: Any = None, input_tables: list[Url] | None = None) -> None: ...
