import enum
import threading
from _typeshed import Incomplete
from collections.abc import Generator, Sequence
from dataclasses import dataclass
from tlc.core.objects.tables.system_tables.indexing import _BlacklistExceptionHandler, _ScanIterator, _ScanUrl, blacklist_visitor as blacklist_visitor
from tlc.core.objects.tables.system_tables.timestamp_helper import TimestampHelper as TimestampHelper
from tlc.core.url import Url as Url
from tlc.core.url_adapter import UrlAdapterDirEntry as UrlAdapterDirEntry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from typing import Literal

logger: Incomplete

class _RetryHandler:
    """Manages retry logic for worker thread exceptions."""
    def __init__(self, interval: float, max_retries: int = 5) -> None: ...
    def handle_exception(self, exc: Exception) -> bool:
        """Handle an exception and determine if retry should continue.

        :param exc: The exception that occurred
        :return: True if retry should continue, False if max retries exceeded
        """
    def on_success(self) -> None:
        """Reset retry state after successful operation."""

class _TimestampFileState(enum.Enum):
    """State of a timestamp file for a given context."""
    INITIAL = 'initial'
    VALID = 'valid'
    DISABLED = 'disabled'
    MISSING = 'missing'
    ERROR = 'error'

class _ScanUrlHandler:
    def __init__(self, scan_url: _ScanUrl, blacklist_config: list[_BlacklistExceptionHandler] | None, tag: str = '', stop_event: threading.Event | None = None, file_extensions: Sequence[str] | None = None) -> None: ...
    @property
    def root_url(self) -> Url: ...
    @property
    def cached_contexts(self) -> Sequence[str]:
        """Get cached contexts from the last scan. Returns empty list if not yet scanned.

        This property returns the cached list of contexts discovered during the last scan.
        It does not trigger LIST operations. Contexts are populated during actual scanning
        via iter_nested(). On the first scan, this will be empty until contexts are discovered.

        :returns: List of cached context names (e.g., project names for project layouts)
        """
    @staticmethod
    def create_iterator(scan_url: _ScanUrl, blacklist_config: list[_BlacklistExceptionHandler] | None, tag: str, stop_event: threading.Event | None = None, file_extensions: Sequence[str] | None = None) -> _ScanIterator:
        """Get the optimal iterator for a scan URL."""
    def scan(self, force: bool = False) -> bool:
        """Perform a scan and return whether changes were detected.

        :param force: Whether to force a rescan regardless of other conditions
        :return: Whether any changes were detected
        """
    def scan_contexts(self, force: bool = False) -> Generator[tuple[str, bool], None, None]:
        """Perform a nested scan of all contexts, yielding which contexts were updated.

        This method is used for partial updates, allowing the caller to process each context's changes
        as they are detected. The internal state is updated during scanning.

        :param force: Whether to force a rescan regardless of other conditions
        :yield: Tuple of (context_name, whether_changed) for each context scanned
        """
    def get_index(self, context: str | None = None) -> list[UrlAdapterDirEntry]:
        """Get the current index and whether changes were detected.

        :param force: Whether to force a rescan regardless of other conditions
        :return: Tuple of (all entries, whether changes were detected)
        """
    def get_timestamp_url(self, context_name: str | None = None) -> Url: ...
    @staticmethod
    def are_entries_equal(previous_entries: Sequence[UrlAdapterDirEntry] | None, current_entries: Sequence[UrlAdapterDirEntry]) -> bool:
        """
        Compare two (sorted) sequences of directory entries for equality.

        :param previous_entries: Previous scan results, or None if this is first scan
        :param current_entries: Current scan results to compare against
        :return: True if sequences are identical, False if they differ
        """

@dataclass(order=True)
class _ScanToken:
    """Represents a specific scan operation"""
    id: int
    progress: float = ...
    completed: bool = ...
    def next(self) -> _ScanToken:
        """Create a new scan token for the next scan operation.

        This creates a new token with an incremented ID and resets progress to 0.
        The original token remains unchanged.

        :return: A new scan token with incremented ID
        """
    def set_complete(self) -> None:
        """Mark the token as complete and set progress to 1.0."""
    def is_complete(self) -> bool:
        """Check if the token is complete."""
    def set_progress(self, progress: float) -> None:
        """Set the progress value, ensuring it doesn't exceed 1.0."""

@dataclass
class _ScanOperation:
    """Represents a scan operation with its token and scan details."""
    token: _ScanToken
    root: Url | None
    context_name: str | None
    entries: Sequence[UrlAdapterDirEntry] | None
    state: Literal['complete', 'noop', 'removal', 'content']
    @classmethod
    def complete(cls, token: _ScanToken) -> _ScanOperation:
        """Create a complete scan operation for signaling purposes.

        This means that the series of operations denoted by a specific _ScanToken.id have completed.
        This is typically used to wait for a series of operations to complete.
        """
    def is_complete(self) -> bool:
        """A complete operation is one that has completed all the operations denoted by the token."""
    @classmethod
    def noop(cls, token: _ScanToken) -> _ScanOperation:
        """Create a no-operation scan operation for signaling purposes.

        This is used when we need to maintain token sequence but have no actual work to do.
        """
    def is_noop(self) -> bool:
        """A noop operation is one that has no entries and is not completed."""
    @classmethod
    def removal(cls, token: _ScanToken, root: Url) -> _ScanOperation:
        """Create a scan operation for removing a scan URL."""
    def is_removal(self) -> bool:
        """A removal operation is one that has a root URL and no entries."""

class _UrlIndexingWorker(threading.Thread):
    """An indexer that crawls a directory and indexes the files in it.

    This is an indexer that repeatedly performs a scan of its directories and indexes the files in it. It runs in
    a separate thread to allow for asynchronous scanning, but has an idle overhead. The indexer can be stopped and
    started again.

    The actual scanning of the directory is done by ScanIterators that wrap around URL-adapters.
    """
    def __init__(self, interval: float, blacklist_config: list[_BlacklistExceptionHandler], tag: str = '', stop_event: threading.Event | None = None, file_extensions: Sequence[str] | None = None) -> None: ...
    @property
    def new_index_event(self) -> threading.Event: ...
    def get_scan_urls(self) -> list[_ScanUrl]:
        """Get list of scan URLs currently being monitored."""
    def touch(self) -> None:
        """Update the timestamp of the last activity to prevent the indexer from going idle."""
    def add_scan_url(self, url_config: _ScanUrl) -> None:
        """Adds a new URL to the list of URLs to be scanned by the indexer."""
    def remove_scan_url(self, url_config: _ScanUrl) -> None:
        """Removes a URL from the list of URLs to be scanned by the indexer."""
    def handle_pending_scan_urls(self, token: _ScanToken) -> None:
        """Handle pending scan URLs.

        Updates the scan_urls to be scanned and pushes relevant _ScanOperation updates on the worker queue.
        """
    def run(self) -> None:
        """Method representing the thread's activity."""
    def scan(self, token: _ScanToken, incremental: bool, force: bool = False) -> bool:
        """Perform a scan for all handlers and incrementally push ScanOperations to the work queue.

        If incremental is False, the scan will be interrupted if a complete reindex cycle is requested.

        :param token: The scan token to update progress on
        :param incremental: Whether this is an incremental scan
        :param force: Whether to force a rescan
        :return: Whether the scan completed
        """
    def request_index(self, force: bool = False) -> _ScanToken:
        """Request a re-index operation without waiting for completion.

        This method is not reentrant and must only be called from the main thread.
        Multiple calls are allowed but will log a warning if a reindex is already in progress.

        :param force: Whether to force a rescan regardless of other conditions
        :return: The scan token for tracking the reindex operation
        :raises RuntimeError: If the indexing worker is not started
        """
    def wait_for_complete_reindex(self, timeout: float | None = None, force: bool = False) -> tuple[bool, _ScanToken]:
        """Wait for a complete reindex operation to finish.

        This method is not reentrant and must only be called from the main thread.
        If a reindex operation is already in progress, raises RuntimeError.

        :param timeout: Maximum time to wait in seconds, or None to wait indefinitely
        :param force: Whether to force a rescan regardless of other conditions
        :return: Tuple of (success, token) where success indicates if the reindex completed
            within the timeout period
        :raises RuntimeError: If the indexing worker is not started or if a reindex is already in progress
        """
    def stop(self) -> None:
        """Method to signal the thread to stop its activity.

        This doesn't terminate the thread immediately, but flags it to exit when it finishes its current iteration.
        """
    def join(self, timeout: float | None = None) -> None:
        """Wait for the thread to join.

        This method will block until the thread has finished its current iteration and is ready to join.
        """
