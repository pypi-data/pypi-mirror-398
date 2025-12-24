from _typeshed import Incomplete
from concurrent.futures import Future
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import MalformedContentError as MalformedContentError, NotRegisteredError as NotRegisteredError, ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.project_context import ProjectContext as ProjectContext
from tlc.core.tlc_core_threadpool import submit_future as submit_future
from tlc.core.transaction_closer import TransactionCloser as TransactionCloser
from tlc.core.url import Scheme as Scheme, Url as Url
from tlc.core.url_adapter import UrlAdapter as UrlAdapter
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry

logger: Incomplete

class ObjectRegistry:
    """
    Maintains a list of currently existing 3LC objects, and provides
    functionality for deserializing objects from JSON strings.
    """
    @staticmethod
    def drop_cache() -> None:
        """Probably just a temporary workaround until we resolve ObjectRegistry semantics."""
    @staticmethod
    def add_object_at_url(obj: Object, url: Url) -> None:
        """Add the given object with the given URL"""
    @staticmethod
    def consider_indexing_callbacks(obj: Object, url: Url, event_type: _IndexerCallbackEventType) -> None:
        """Maybe notify interested indexers of new objects for indexing

        Improve indexing performance by push notifications, if wanted.
        Normally set up when creating indexing singletons.
        """
    @staticmethod
    def get_object_from_url(url: Url) -> Object | None:
        """Get or create object from URL synchronously"""
    @staticmethod
    def delete_object_from_url(url: Url) -> None:
        """
        Tries to delete an object from an URL synchronously

        Tries to delete the Url using available adapters
        Always removes the object from the registry's internal caches
        """
    @staticmethod
    def delete_object_from_url_async(url: Url) -> Future:
        """Tries to delete an object from an URL asynchronously

        Tries to delete the Url using available adapters
        This also removes the object from the registry's internal caches"""
    @staticmethod
    def get_or_create_object_from_url(url: Url) -> Object:
        """Get or create object from URL synchronously

        :param url: The URL to read the object from. This URL must be absolute.
        :raises ValueError: If the URL is not absolute.
        """
    @staticmethod
    def get_or_create_object_from_url_async(url: Url) -> Future:
        """Get or create object from URL asynchronously

        :param url: The URL to read the object from. This URL must be absolute.
        :raises ValueError: If the URL is not absolute.
        """
    @staticmethod
    def write_object_to_url(obj: Object, url: Url) -> None:
        """Write an object to a URL synchronously"""
    @staticmethod
    def write_object_to_url_async(obj: Object, url: Url) -> Future:
        """Write an object to a URL asynchronously"""
