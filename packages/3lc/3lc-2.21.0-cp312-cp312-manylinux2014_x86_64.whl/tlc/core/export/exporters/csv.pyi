from csv import Dialect
from tlc.core.export.exporter import Exporter as Exporter, register_exporter as register_exporter
from tlc.core.objects.table import Table as Table
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from typing import Any

class CSVExporter(Exporter):
    """Exporter for the CSV format."""
    priority: int
    supported_format: str
    @classmethod
    def can_export(cls, table: Table, output_url: Url) -> bool: ...
    @classmethod
    def serialize(cls, table: Table, output_url: Url, weight_threshold: float = 0.0, dialect: str | Dialect | type[Dialect] = 'excel', exclude_header: bool = False, **kwargs: Any) -> str:
        '''Serialize a table to a CSV string.

        :param table: The table to serialize
        :param weight_threshold: The minimum weight of a row to be included in the output
        :param dialect: The dialect to use for the CSV output. This can be a string like "excel" or "unix". If you are
            not using the CLI tool, but are instead using the Python API, you can also pass a Dialect object or a
            subclass of Dialect.
        :param exclude_header: Exclude the header row in the output
        :return: A CSV string representing the table
        '''
