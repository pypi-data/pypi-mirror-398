import abc
import threading
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from collections.abc import Generator, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from tlc.core.object_type_registry import NotRegisteredError as NotRegisteredError
from tlc.core.url import Url as Url
from tlc.core.url_adapter import UrlAdapterDirEntry as UrlAdapterDirEntry
from types import TracebackType
from typing import Any, Callable, Literal, TypedDict

logger: Incomplete

class _ScanUrl(TypedDict, total=False):
    """A dictionary representing a URL to scan with options."""
    url: Url
    layout: Literal['single_dir', 'project', 'file']
    object_type: Literal['table', 'run', 'config']
    interval: float | None
    create_default_dirs: bool | None
    static: bool | None

@dataclass
class _UrlIndex:
    """A private class used to store Url index details.

    :param url: The URL of the file.
    :param m_time: The last modified time of the Url, as reported by scan.
    :param is_package: Whether the Url is a package, i.e. a directory containing a 3LC object file.
    :param base_dir: The base directory of the file.
    """
    url: Url
    m_time: datetime | None
    is_package: bool
    base_dir: Url

class _StopScanIteration(Exception):
    """An exception to signal that scanning stopped."""

@dataclass
class _BlacklistEntry:
    """A class for representing Urls that are being held in a blacklist.

    :param url: The URL of the file.
    :param exception: The exception that caused the Url to be blacklisted.
    :param expiry_time: The expiry time of the blacklist entry.
    :param retries: The number of retries currently performed for this Url.
    """
    url: Url
    exception: BaseException
    expiry_time: datetime | None
    retries: int

def blacklist_message(url: Url, exception: BaseException, backoff: timedelta | None) -> str: ...
def resolve_message(url: Url, exception: BaseException, force: bool) -> str: ...

@dataclass
class _BlacklistExceptionHandler:
    """
    A class for handling exceptions encountered during handling of URLs.

    This class implements the logic for handling exceptions encountered during indexing of URLs. It includes the
    exception type to handle, the backoff function to compute the next retry time, and the description of the handler.

    :param type[BaseException] exception_type: The type of exception to handle.
    :param Callable[[int], timedelta] | None expiration_func: A function to compute the next expiration based on the
        retry number.
    :param Callable[[Url, BaseException, timedelta | None], str] blacklist_message: A function to generate a message
        when blacklisting a URL.
    :param int blacklist_log_level: The log level at which blacklist messages are logged. Default is logging.WARNING.
    :param Callable[[Url, BaseException,bool], str] resolve_message: A function to generate a message when resolving a
        URL.
    :param int resolve_log_level: The log level at which resolve messages are logged. Default is logging.INFO.
    :param str description: A description of the handler. Default is an empty string.
    """
    exception_type: type[BaseException]
    expiration_func: Callable[[int], timedelta] | None
    blacklist_message: Callable[[Url, BaseException, timedelta | None], str] = ...
    blacklist_log_level: int = ...
    resolve_message: Callable[[Url, BaseException, bool], str] = ...
    resolve_log_level: int = ...
    description: str = ...
    @classmethod
    def from_any(cls, conf: Any) -> _BlacklistExceptionHandler: ...

class _NotRegisteredHandler(_BlacklistExceptionHandler):
    """A handler for exceptions generated encountering unregistered types

    Blacklist URLs as normal but only warn once for every unregistered type-name.
    """
    def __init__(self) -> None: ...

class _UrlBlacklist:
    """Manages exceptions encountered during for example URL indexing, with configurable logging and expiry times.

    This class includes capabilities for adding, querying, updating, and resolving URLs in a blacklist. It utilizes a
    list of handler instances to provide distinct handling for various types of exceptions.

    :param config: A list of _BlackListExceptionHandlers that configures the blacklist for handling different errors.
    """
    config: Incomplete
    blacklist: dict[Url, _BlacklistEntry]
    exempt_exceptions: list[type[BaseException]]
    def __init__(self, config: Sequence[_BlacklistExceptionHandler], exempt: Sequence[type[BaseException]] = ...) -> None: ...
    def has_blacklisted_urls(self) -> bool:
        """Check if there are any blacklisted URLs.

        Returns:
            bool: True if there are any blacklisted URLs, False otherwise
        """
    def get_earliest_resolve_time(self) -> datetime | None:
        """Get the earliest time when a blacklisted URL will be resolved.

        :returns: The earliest expiry time of any blacklisted URL, or None if no expiry times exist
        """
    def handle_exception(self, url: Url, exception: BaseException) -> bool: ...
    def is_blacklisted(self, url: Url) -> bool: ...
    def resolve(self, url: Url) -> bool:
        """Forcefully resolve the URL in the blacklist.

        This removes the URL from the blacklist if it is present even if the expiry is not yet met.
        :param url: The URL to resolve.
        :return bool: Returns whether the URL was blacklisted.
        """

class _BlacklistVisitor:
    """A context manager for visiting urls in the blacklist

    This manager correctly handles exceptions and updates the blacklist accordingly.
    """
    blacklist: Incomplete
    url: Incomplete
    is_blacklisted: bool
    skip: bool
    def __init__(self, blacklist: _UrlBlacklist, url: Url) -> None: ...
    def __enter__(self) -> _BlacklistVisitor: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, _: TracebackType) -> bool | None: ...

def blacklist_visitor(blacklist: _UrlBlacklist, url: Url) -> _BlacklistVisitor:
    """Create a blacklist visitor that automatically sets skip if the URL is blacklisted.

    This is a convenience function for the common pattern of creating a blacklist visitor
    and setting skip if the URL is blacklisted.

    :param blacklist: The blacklist to check against
    :param url: The URL to check
    :return: A configured _BlacklistVisitor instance
    """

class _ScanIterator(ABC, metaclass=abc.ABCMeta):
    """Abstract base class for iterating over Urls and finding relevant files.

    This class provides an iterator interface for iterating over directories containing 3LC objects. It is intended to
    be used as a base class for classes that implement directory iteration for different storage systems.

    :param scan_urls: The URL of the directory to iterate over.
    :param extensions: A list of file extensions to consider while scanning.
    :param tag: A tag to identify the iterator.
    :param blacklist_config: A list of _BlacklistExceptionHandlers that configures the blacklist for handling different
        errors.
    """
    scan_url: Incomplete
    extensions: Incomplete
    filenames: Incomplete
    tag: Incomplete
    blacklist: Incomplete
    is_first_scan: bool
    def __init__(self, scan_url: _ScanUrl, extensions: Sequence[str], filenames: Sequence[str], tag: str, blacklist_config: Sequence[_BlacklistExceptionHandler] | None, stop_event: threading.Event | None = None) -> None: ...
    @property
    def root(self) -> Url: ...
    @abstractmethod
    def scan(self) -> Generator[UrlAdapterDirEntry, None, None]:
        """Perform a recursive scan and yield all resulting directory entries.

        This is the top level entry point for the iterator."""
    def iter_nested(self) -> Generator[tuple[str, Generator[UrlAdapterDirEntry, None, None]], None, None]:
        """Iterate over nested content in a uniform way.

        This method yields tuples of (context_name, entries) where:
        - context_name is a string identifier for the context (e.g. project name) or None for non-nested content
        - entries is a generator that yields all the relevant entries for that context

        The default implementation treats everything as a single context.

        :yields: Tuples of (context_name, entries) where entries is a generator of UrlAdapterDirEntry
        """
    @property
    def contexts(self) -> Sequence[str]:
        '''Get the contexts for the iterator.

        :returns: A list of context names. Default is one context named "".
        '''
    def __iter__(self) -> Generator[UrlAdapterDirEntry, None, None]:
        """Allow ScanIterator to be used as a generator without calling scan()."""

@dataclass
class _UrlContent:
    """Data class to represent the content of a Url along with metadata.

    :param url: The URL
    :param base_dir: The base directory of the Url.
    :param m_time: The last modification time of the Url.
    :param content: The parsed JSON content of the Url.
    """
    url: Url
    base_dir: Url
    m_time: datetime | None
    content: dict[str, object]
