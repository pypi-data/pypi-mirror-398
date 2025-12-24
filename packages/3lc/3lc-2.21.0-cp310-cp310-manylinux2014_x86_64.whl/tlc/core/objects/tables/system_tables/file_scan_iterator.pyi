import threading
from _typeshed import Incomplete
from collections.abc import Generator, Sequence
from tlc.core.objects.tables.system_tables.indexing import _BlacklistExceptionHandler, _ScanIterator, _ScanUrl, blacklist_visitor as blacklist_visitor
from tlc.core.url_adapter import UrlAdapterDirEntry as UrlAdapterDirEntry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry

logger: Incomplete

class _FileScanIterator(_ScanIterator):
    """An iterator that scans a single file like object."""
    def __init__(self, scan_url: _ScanUrl, tag: str, blacklist_config: Sequence[_BlacklistExceptionHandler] | None, stop_event: threading.Event | None) -> None: ...
    def scan(self) -> Generator[UrlAdapterDirEntry, None, None]: ...
