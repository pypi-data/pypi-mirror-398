from tlc.core.objects.table import ImmutableDict as ImmutableDict, Table as Table
from tlc.core.table_row_serializer import TableRowSerializer as TableRowSerializer
from tlc.core.table_row_serializer_registry import TableRowSerializerRegistry as TableRowSerializerRegistry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry

class ParquetTableRowSerializer(TableRowSerializer):
    """
    An object which can pull rows from a table and serialize them to Parquet format
    """
    def internal_serialize(self, table: Table) -> bytes:
        """Serializes all rows/columns of a table and writes the serialized contents to a cache
        file or folder.

        Will write the serialized contents to table.row_cache_url.

        If table.row_cache_populated is True, this method simply reads the cache and returns
        the contents.

        If table.row_cache_populated is False, this method will populate the cache and then
        read the cache and return the contents.

        :param table: The table to serialize
        :return: The serialized contents
        """
