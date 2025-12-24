from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.objects.tables.system_tables.indexing import _ScanUrl
from tlc.core.objects.tables.system_tables.indexing_table import IndexingTable as IndexingTable
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from tlc.core.url_adapters import ApiUrlAdapter as ApiUrlAdapter
from typing import Any

logger: Incomplete

class RunIndexingTable(IndexingTable):
    """A specialized indexing table for Run objects fetched from URLs.

    This table is designed to manage Run objects. Each row in this table corresponds
    to a Run object that is fetched from a URL. It extends from the generic
    `IndexingTable` to provide functionalities specifically optimized for handling Run objects.

    :Example:

    ```python
    table = RunIndexingTable.instance()
    table.wait_for_next_index()
    for row in table.table_rows:
        print(row)
    ```

    :Closing Comments:

    - **Singleton Pattern**: This class implements the Singleton pattern.
      Always use `RunIndexingTable.instance()` to get the singleton instance.

    :param url: The URL from which this table can be read.
    :param scan_urls: A list of URLs to scan for runs.
    :param scan_wait: Time to wait before requeuing a new scan, in seconds.
    :param init_parameters: Any initialization parameters.

    :raises ValueError: If some conditions, such as invalid URLs, are not met.
    """
    run_indexing_table_instance: RunIndexingTable | None
    def __init__(self, url: Url | None = None, project_scan_urls: Sequence[Url] | None = None, extra_scan_urls: Sequence[Url] | None = None, scan_urls: Sequence[_ScanUrl] | None = None, scan_wait: float | None = None, create_default_dirs: bool | None = None, init_parameters: Any = None) -> None: ...
    @staticmethod
    def instance() -> RunIndexingTable:
        """
        Returns the singleton RunIndexingTable object
        """
    def should_consider_object(self, obj: Object) -> bool:
        """Only consider Runs"""
