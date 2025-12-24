import weakref
from _typeshed import Incomplete
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_INDEX as NUMBER_ROLE_INDEX
from tlc.core.object import Object as Object
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry, _IndexerCallbackEventType
from tlc.core.object_type_registry import MalformedContentError as MalformedContentError, NotRegisteredError as NotRegisteredError, ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.system_tables.indexing import _ScanUrl, blacklist_visitor as blacklist_visitor
from tlc.core.objects.tables.system_tables.timestamp_helper import TimestampHelper as TimestampHelper
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Int32Value as Int32Value, MapElement as MapElement, ObjectTypeStringValue as ObjectTypeStringValue, Schema as Schema, StringValue as StringValue, UrlStringValue as UrlStringValue
from tlc.core.url import Url as Url
from tlc.utils.datetime_helper import DateTimeHelper as DateTimeHelper
from typing import Any, Literal

logger: Incomplete

@dataclass
class _PendingItem:
    obj: weakref.ref[Object]
    base_dir: Url
    op_type: Literal['Add', 'Delete']
    num_updates: int
    mtime: datetime

class IndexingTable(Table):
    """The base class for tables which are populated by scanning the contents of a URL.

    The scanning can be limited to a particular object type (e.g. Run).

    :param url: The URL of the table.
    :param created: The creation timestamp of the table.
    :param row_cache_url: The URL of the row cache.
    :param row_cache_populated: Indicates whether the row cache is populated.
    :param scan_urls: The URLs to be scanned.
    :param constrain_to_type: The type of objects to be included in the table.
    :param init_parameters: Any additional initialization parameters.

    """
    scan_urls: list[_ScanUrl]
    constrain_to_type: str
    def __init__(self, url: Url | None = None, created: str | None = None, row_cache_url: Url | None = None, row_cache_populated: bool | None = None, project_scan_urls: Sequence[Url] | None = None, extra_scan_urls: Sequence[Url] | None = None, scan_urls: Sequence[_ScanUrl] | None = None, constrain_to_type: str | None = None, scan_wait: float | None = None, file_extensions: Sequence[str] | None = None, create_default_dirs: bool | None = None, init_parameters: Any = None) -> None: ...
    @property
    def running(self) -> bool:
        """Whether the indexing table is currently running"""
    def add_scan_url(self, scan_url: _ScanUrl) -> None:
        """Adds a Scan URL to the indexing table.

        The URL will be added to the list of URLS scanned to populate the table.
        Any new content is added to the table on the next indexing cycle.
        """
    def remove_scan_url(self, scan_url: _ScanUrl) -> None:
        """Removes a Scan URL from the indexing table.

        The URL will be removed from the list of URLs scanned to populate the table.
        Any new content is removed from the table on the next indexing cycle.
        """
    def add_extra_scan_urls(self, scan_urls: list[Url | str]) -> None:
        """Add extra scan urls to this indexing table

        If the indexing table is running changes will be propagated to worker threads.
        """
    def add_project_scan_urls(self, project_scan_urls: list[Url | str]) -> None:
        """Add scan urls to this indexing table

        If the indexing table is running changes will be propagated to worker threads.
        """
    def consider_indexing_object(self, obj: Object, url: Url, event_type: _IndexerCallbackEventType) -> bool: ...
    def add_indexing_object(self, obj: Object, url: Url) -> bool:
        """Adds a URL to the wait list (if it's considerable)"""
    def delete_indexing_object(self, obj: Object, url: Url) -> bool:
        """Adds a URL to the delete wait list (if it's considerable)"""
    def should_consider_url(self, url: Url) -> bool:
        """Whether the indexer should consider the given URL for indexing"""
    def should_consider_object(self, obj: Object) -> bool:
        """Only consider registered types that are derived from the constrain_to_type"""
    def start(self) -> None: ...
    rows: list[Any]
    row_count: Incomplete
    def ensure_dependent_properties(self) -> None:
        '''The rows of an IndexingTable are considered dependent properties and this is where the table is populated
        with the objects from the indexed URLs

        IndexingTable deviates from the immutability of the Table class and repeated calls to this function will
        re-populate the table with the latest indexed data.

        A call to this function is a no-op if no new data is available, when the table is queried it will simply return
        the last populated index.

        If new data is available, from indexing or "fast-track", it will re-populate the table with the new data.
        '''
    def append_row(self, row: Any, location_index: int) -> None:
        """Register row in owned row list"""
    def __len__(self) -> int: ...
    def stop(self, timeout: float | None = ...) -> None:
        """Stop the indexing table and wait for the reader and indexing workers to finish.

        :param timeout: timeout in seconds. The function will block until the reader and indexing workers are finished
            or the timeout is reached unless timeout is None, in which case the function will block indefinitely.
        """
    def request_reindex(self, force: bool = False) -> int:
        """Trigger a reindex of the table.

        :param force: Whether to force the reindex even if it is already in progress.
        :return: The request token for the reindex.
        """
    def wait_for_complete_index(self, timeout: float | None = None, force: bool = False) -> bool:
        """Wait for a complete indexing cycle to finish

        :param timeout: timeout in seconds. The function will block until the next indexing cycle is complete or the
            timeout is reached unless timeout is None, in which case the function will block indefinitely.
        :param force: Whether to force the reindex even if it is already in progress.
        :return: True if the next index is available, False if timed out
        """
    @property
    def counter(self) -> float:
        """A counter that is incremented every time the table could be updated with new data"""
