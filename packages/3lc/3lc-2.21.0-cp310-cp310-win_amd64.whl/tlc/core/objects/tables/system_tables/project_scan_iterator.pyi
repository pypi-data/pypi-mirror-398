import abc
import threading
from _typeshed import Incomplete
from abc import abstractmethod
from collections.abc import Generator, Sequence
from tlc.core.objects.tables.system_tables.indexing import _BlacklistExceptionHandler, _ScanIterator, _ScanUrl, blacklist_visitor as blacklist_visitor
from tlc.core.project_context import disabled_project_context as disabled_project_context
from tlc.core.url import Url as Url
from tlc.core.url_adapter import UrlAdapterDirEntry as UrlAdapterDirEntry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry

logger: Incomplete

class _ProjectScanIterator(_ScanIterator, metaclass=abc.ABCMeta):
    """Base class for ScanIterators that scan 3LC project folder layouts."""
    def __init__(self, scan_url: _ScanUrl, extensions: Sequence[str], filenames: Sequence[str], tag: str, blacklist_config: Sequence[_BlacklistExceptionHandler] | None, stop_event: threading.Event | None) -> None: ...
    @staticmethod
    def projects_readme() -> str: ...
    @staticmethod
    def default_project_readme() -> str: ...
    @abstractmethod
    def scan_project_url(self, project_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    @property
    def contexts(self) -> Sequence[str]:
        """Lists all projects directories under the root URL."""
    is_first_scan: bool
    def iter_nested(self) -> Generator[tuple[str, Generator[UrlAdapterDirEntry, None, None]], None, None]:
        """Iterate over projects and their contents separately.

        This method yields tuples of (project_name, project_contents) where project_contents is a generator
        that yields all the relevant entries for that project.

        :yields: Tuples of (project_name, project_contents) where project_contents is a generator of UrlAdapterDirEntry
        """
    def scan_root(self, create_default_dirs: bool) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan(self) -> Generator[UrlAdapterDirEntry, None, None]:
        """Scan the 3LC project layout Scan URLS and recursively yield directory entries."""

class _ProjectRunScanIterator(_ProjectScanIterator):
    """A scan iterator that yields all Runs from a 3LC directory layout.

    Runs are stored in a fixed folder structure:
        - Pattern: <projects_dir>/runs/<run_name>
        - Glob: <projects_dir>/*/runs/*
    """
    def __init__(self, scan_url: _ScanUrl, tag: str, blacklist_config: Sequence[_BlacklistExceptionHandler] | None, stop_event: threading.Event | None) -> None: ...
    def scan_project_url(self, project_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_runs_url(self, runs_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_run_url(self, run_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...

class _ProjectTableScanIterator(_ProjectScanIterator):
    """A scan iterator that yields all Tables from a 3LC directory layout.

    Tables are stored in a fixed folder structure:
        - Pattern: <projects_dir>/<project_name>/datasets/<dataset_name>/tables/<table_name>
        - Glob: <projects_dir>/*/datasets/*/tables/*/


    :param scan_urls: A list of URLs of directories to scan.
    """
    def __init__(self, scan_url: _ScanUrl, tag: str, blacklist_config: Sequence[_BlacklistExceptionHandler] | None, stop_event: threading.Event | None) -> None: ...
    def scan_project_url(self, project_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_datasets_url(self, datasets_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_dataset_url(self, dataset_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_tables_url(self, tables_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
    def scan_table_url(self, table_url: Url, depth: int) -> Generator[UrlAdapterDirEntry, None, None]: ...
