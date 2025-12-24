import abc
import argparse
from _typeshed import Incomplete
from abc import abstractmethod
from collections.abc import Iterator
from tlc.core.objects.table import Table as Table, TableRow as TableRow
from tlc.core.project_context import disabled_project_context as disabled_project_context
from tlc.core.schema_helper import SchemaHelper as SchemaHelper
from tlc.core.url import Url as Url
from typing import Any, ClassVar

logger: Incomplete

class Exporter(metaclass=abc.ABCMeta):
    """The base class for all Exporters.

    Exporters are used to export tables to various formats, typically after a user is done cleaning their data with 3LC.
    Subclasses of Exporter should be registered using the `register_exporter` decorator, which makes them available for
    use in `Table.export()`. Subclasses of exporter must implement the `serialize` method, which serializes a table to a
    string which can be written to a URL. Subclasses can also override the `can_export` method, which determines whether
    the exporter can export a given table to a given URL. If `can_export` is not overridden, it will return False for
    all tables and URLs, and will only be used if the `format` argument is specified in `Table.export()`.

    Subclasses of Exporter must define the class attribute `supported_format`, which is a string indicating the format
    that the exporter supports. This string is used by `Table.export()` to determine which exporter to use. Whenever the
    `format` argument is not specified in `Table.export()`, it will call `can_export` for all registered exporters to
    find compatible ones. If multiple exporters are compatible, the one with the highest `priority` will be used, which
    is an optional class attribute that defaults to 0.

    :cvar exporters: A dict mapping formats to exporter types. This dict is populated by the `register_exporter`
        decorator.
    :cvar priority: An integer indicating the priority of the exporter. This is used to break ties when multiple
        exporters are compatible with a given table and URL. The exporter with the highest priority will be used.
    :cvar supported_format: A string indicating the format that the exporter supports. This string is used by
        `Table.export()` to determine which exporter to use.
    """
    exporters: ClassVar[dict[str, type[Exporter]]]
    priority: int
    supported_format: str
    @classmethod
    def export(cls, table: Table, output_url: Url, format: str, weight_threshold: float, **kwargs: object) -> None:
        """Export a table to a URL.

        :param table: The table to export
        :param output_url: The URL to export to
        :param format: The format indicating which exporter to use
        :param weight_threshold: The weight threshold to use for exporting. If the table has a weights column, rows
            with a weight below this threshold will be excluded from the export.
        :param kwargs: Additional arguments for the `serialize` method of the applied subclass of Exporter. Which
            arguments are valid depends on the format. See the documentation for the subclasses of Exporter for more
            information.
        """
    @classmethod
    def register_exporter(cls, exporter_type: type[Exporter]) -> None:
        """Register an exporter type by adding it to the `exporters` dict, with the format it supports as the key.

        :param exporter_type: The exporter type to register
        """
    @classmethod
    def can_export(cls, table: Table, output_url: Url) -> bool:
        """Check if the exporter can export the given `table` to the given `output_url`. This method is used by
        `Table.export()` whenever the `format` argument is not specified. In these cases, it will be called for all
        registered exporters, so it should be as fast as possible. `can_export` can be thought of as codifying the
        assumptions of `serialize` for any given exporter.

        :param table: The table to export
        :param output_url: The URL to export to
        :return: True if the exporter can export the table to the given URL, False otherwise
        """
    @staticmethod
    def remaining_table_rows(table: Table, weight_threshold: float) -> Iterator[TableRow]:
        """Return an iterator of the remaining rows in the table after filtering out rows with a weight below the given
        threshold.

        :param table: The table to filter
        :param weight_threshold: The weight threshold
        :return: An iterator of the remaining rows in the table
        """
    @classmethod
    @abstractmethod
    def serialize(cls, table: Table, output_url: Url, weight_threshold: float = 0.0, **kwargs: Any) -> str:
        """Serialize a table to a string which can be written to a Url.

        :param table: The table to serialize
        :param kwargs: Any additional arguments
        :return: The serialized table
        """
    @classmethod
    def add_registered_exporters_to_parser(cls, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Add arguments to the given parser for all registered exporters.

        :param parser: The parser to add arguments to
        :return: The parser with the added arguments
        """

def register_exporter(exporter_type: type[Exporter]) -> type[Exporter]:
    """A decorator for registering an exporter type.

    Using this decorator above the class definition of an exporter
    makes it available for use in `Table.export()`.
    """
def infer_format(table: Table, output_url: Url) -> str:
    """Infer the most suitable export format given a table and an output url.

    This function is used by
    `Table.export()` whenever the `format` argument is not specified.

    :param table: The table to export
    :param output_url: The URL to export to
    :return: The format of the table
    """
