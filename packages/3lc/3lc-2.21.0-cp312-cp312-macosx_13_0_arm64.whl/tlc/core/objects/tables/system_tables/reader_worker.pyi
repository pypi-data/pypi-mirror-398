import queue
import threading
from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.core.objects.tables.system_tables.indexing import _UrlContent
from tlc.core.objects.tables.system_tables.indexing_worker import _ScanOperation, _ScanToken
from tlc.core.url import Url as Url
from tlc.core.url_adapter import UrlAdapterDirEntry as UrlAdapterDirEntry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry

logger: Incomplete

class _UrlReaderWorker(threading.Thread):
    '''A threaded class that periodically reads files from a _ThreadedDirectoryFileIndexer instance.

    :Example:

    ```python
    scan_urls = ["./path/to/dir", "./another/path"]
    indexer = _UrlIndexingWorker(scan_urls)
    file_reader = _UrlReaderWorker(indexer)
    file_reader.start()
    # Get the file contents
    files = file_reader.get_files()
    ```

    :param indexer: An instance of _UrlIndexingWorker which provides the index scanning.
    '''
    def __init__(self, work_queue: queue.Queue[_ScanOperation], tag: str = '', stop_signal: threading.Event | None = None) -> None: ...
    def remove_scan_url(self, url: Url) -> None:
        """Remove a scan URL from the reader."""
    @property
    def indexer_token(self) -> _ScanToken:
        """The last processed token from the indexing worker."""
    @property
    def token(self) -> _ScanToken:
        """The current token for the reader state."""
    def run(self) -> None:
        """Method representing the thread's activity.

        Do not call this method directly. Use the start() method instead, which will in turn call this method.
        """
    def start(self) -> None: ...
    def stop(self) -> None:
        """Method to signal the thread to stop its activity.

        This doesn't terminate the thread immediately, but flags it to exit when it finishes its current iteration.
        """
    def process_entries(self, base_url: Url, context_name: str, index: dict[Url, _UrlContent], entries: Sequence[UrlAdapterDirEntry], token: _ScanToken) -> bool:
        """Mutates an existing index based on an incoming Sequence of UrlAdapterDirEntries.

        :param base_url: The base URL for the entries
        :param context_name: The context name for the entries
        :param index: The index to mutate
        :param entries: The entries to process
        :returns: Whether any changes were made to the index
        """
    def process_batch(self, batch: _ScanOperation) -> bool:
        """Process a scan operation."""
    def touch(self) -> None:
        """Update last read timestamp."""
    def get_content(self) -> dict[Url, dict[str, dict[Url, _UrlContent]]]:
        """Returns a deep copy of the latest read Url contents partitioned per base URL.

        :returns: A dictionary of base URL to a dictionary of URL to _UrlContent instances representing the latest read
            contents.
        """
