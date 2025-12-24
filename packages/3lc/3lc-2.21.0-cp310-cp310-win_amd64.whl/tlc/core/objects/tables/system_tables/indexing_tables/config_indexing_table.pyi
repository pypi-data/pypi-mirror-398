from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.core.object import Object as Object
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.objects.tables.system_tables.indexing import _ScanUrl
from tlc.core.objects.tables.system_tables.indexing_table import IndexingTable as IndexingTable
from tlc.core.schema import DictValue as DictValue, Schema as Schema
from tlc.core.url import AliasPrecedence as AliasPrecedence, Url as Url, UrlAliasRegistry as UrlAliasRegistry
from tlc.core.url_adapters import ApiUrlAdapter as ApiUrlAdapter
from tlc.utils.datetime_helper import DateTimeHelper as DateTimeHelper
from tlcconfig.options import ConfigSource
from typing import Any, Literal

logger: Incomplete

class _Config(MutableObject):
    """A private class to encapsulate the Config object.

    A _Config object is an temporary object that encapsulates the content of a config file fetched from a URL."""
    config: dict[str, object]
    config_file_type: Literal[ConfigSource.CONFIG_FILE, ConfigSource.SECONDARY_CONFIG_FILE]
    def __init__(self, url: Url | None = None, created: str | None = None, last_modified: str | None = None, config: object | None = None, config_file_type: ConfigSource | None = None, init_parameters: Any = None) -> None: ...
    @classmethod
    def type_name(cls) -> str:
        """The type name of the class, used to resolve factory methods"""

class ConfigIndexingTable(IndexingTable):
    """A specialized indexing table for Config files fetched from URLs.

    This table is designed to manage Config file objects. Each row in this table corresponds to a config file object
    that is fetched from a URL. It extends from the generic `IndexingTable` to provide functionalities specifically
    optimized for handling external config files embedded with data.

    :Example:

    ```python
    table = ConfigIndexingTable.instance()
    table.wait_for_next_index()
    for row in table.table_rows:
        print(row)
    ```

    :Closing Comments:

    - **Singleton Pattern**: This class implements the Singleton pattern.
      Always use `ConfigIndexingTable.instance()` to get the singleton instance.

    """
    config_indexing_table_instance: ConfigIndexingTable | None
    def __init__(self, url: Url | None = None, scan_urls: Sequence[_ScanUrl] | None = None, init_parameters: Any = None) -> None:
        """
        Initialize a ConfigIndexingTable object.

        :param url: The URL from which this table can be read.
        :param scan_urls: A list of URLs to scan for config files.
        :param init_parameters: Any initialization parameters.

        :raises ValueError: If some conditions, such as invalid URLs, are not met.
        """
    def ensure_dependent_properties(self) -> None:
        """Ensure that the dependent properties are updated.

        Applies aliases from the config files to the global configuration in a deterministic fashion.
        """
    @staticmethod
    def instance() -> ConfigIndexingTable:
        """
        Returns the singleton ConfigIndexingTable object
        """
    def should_consider_object(self, obj: Object) -> bool:
        """Only consider Config objects"""
