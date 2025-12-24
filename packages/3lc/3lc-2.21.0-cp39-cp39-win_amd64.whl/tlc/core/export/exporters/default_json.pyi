from tlc.core.export.exporter import Exporter as Exporter, register_exporter as register_exporter
from tlc.core.objects.table import Table as Table
from tlc.core.url import Url as Url
from tlc.core.utils.progress import track as track
from typing import Any

class DefaultJSONExporter(Exporter):
    """Basic exporter for the JSON format.

    This exporter is used when no other exporter is compatible with the Table,
    and the output path has a .json extension.
    """
    supported_format: str
    priority: int
    @classmethod
    def can_export(cls, table: Table, output_url: Url) -> bool: ...
    @classmethod
    def serialize(cls, table: Table, output_url: Url, weight_threshold: float = 0.0, indent: int = 4, **kwargs: Any) -> str:
        """Serialize a table to a JSON string.

        :param table: The table to serialize
        :param weight_threshold: The minimum weight of a row to be included in the output
        :param indent: The number of spaces to use for indentation in the output
        :return: A JSON string representing the table
        """
