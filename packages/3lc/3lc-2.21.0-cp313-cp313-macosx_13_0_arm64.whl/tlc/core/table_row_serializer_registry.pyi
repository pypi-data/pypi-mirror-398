from abc import ABC
from tlc.core.table_row_serializer import TableRowSerializer as TableRowSerializer
from typing import Any

class TableRowSerializerRegistry(ABC):
    """Maintains a list of currently registered TableRowSerializers."""
    @staticmethod
    def register_table_row_serializer(table_row_serializer: TableRowSerializer) -> None:
        """
        Register a table row serializer in the global registry
        """
    @staticmethod
    def get_table_row_serializer(format_internal_name: str, default_value: TableRowSerializer | None = None) -> TableRowSerializer | None:
        """Get table row serializer  adapter for the given format internal name"""
    @staticmethod
    def serialize(table: Any, wanted_format_internal_name: str = 'parquet') -> bytes:
        """Serializes all rows within a table to a specific binary format

        If no serializer can be resolved for the given format return the 'default_value' if given,
        else raise an exception.
        """
    @staticmethod
    def print_table_row_serializers(line_prefix: str = '') -> None:
        """
        Print all table row serializers.
        """
