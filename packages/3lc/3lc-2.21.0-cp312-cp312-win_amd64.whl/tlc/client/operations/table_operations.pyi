from _typeshed import Incomplete
from tlc.core.objects.table import ImmutableDict as ImmutableDict, Table as Table
from tlc.core.operations import CalculateSchemaContext as CalculateSchemaContext, CalculateValueContext as CalculateValueContext
from tlc.core.operations.operation import Operation as Operation
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from tlc.core.writers.table_writer import TableWriter as TableWriter

logger: Incomplete

def apply_operations(input_table: Table, operations: list[Operation], *, table_url: Url | str | None = None) -> Table:
    """Perform a list of operations on a table, resulting in a new table with one new column per operation.

    :param input_table: The table to apply the operations to.
    :param operations: The operations to apply.
    :param table_url: Optional URL to write the new table to. If None, table will be created next to the input
        table.
    :return: A new table with the results of the operations.
    """
