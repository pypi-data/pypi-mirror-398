from collections.abc import Iterator
from contextlib import contextmanager
from tlc.core.url import Url as Url

def set_bulk_data_url_prefix(prefix: Url | str | None) -> None:
    """Set the global variable for the bulk data URL prefix."""
def set_table_with_bulk_data_url(table_with_bulk_data_url: Url | str | None) -> None:
    """Set the global variable for the table with bulk data URL."""
def increment_and_get_bulk_data_url(column_name: str, suffix: str) -> Url:
    """Get the next bulk data url.

    Increment the bulk data Url index and return a Url corresponding to the given column_name and suffix, and the
    current values of the global bulk data Url prefix and index.

    :param column: The name of the part of the sample to generate the Url for.
    :param suffix: The suffix to be used for the bulk data Url.
    :return: The generated Url.
    """
def relativize_bulk_data_url(bulk_data_url: Url) -> Url:
    """Relativize the given bulk data Url to the Url of the Table with which it is associated."""
def reset_bulk_data_url() -> None:
    """Reset the global bulk data Url prefix and index."""
@contextmanager
def bulk_data_url_context(prefix: Url, table_with_bulk_data_url: Url) -> Iterator[None]:
    """Context manager for bulk data Urls.

    Sets the global bulk data Url prefix to the given prefix, and resets it after the context
    manager exits.

    :param prefix: The prefix to set the global bulk data Url prefix to.
    :param table_with_bulk_data_url: The Url of the Table which all written bulk data Urls within this context will
    be relativized with respect to.
    """
