import datetime
from _typeshed import Incomplete
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pydantic import BaseModel
from tlc.core.project_context import ProjectContext as ProjectContext, disabled_project_context as disabled_project_context
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from typing import Literal

logger: Incomplete

@dataclass
class PendingWrite:
    """
    Represents a pending timestamp write operation.

    :param scheduled_time: Monotonic time when write should occur.
    :param url: URL to write the timestamp for.
    """
    scheduled_time: float
    url: Url
    def __lt__(self, other: PendingWrite) -> bool:
        """Enable heap ordering by scheduled time."""

@dataclass
class UrlWriteState:
    """
    Tracks the write state for a specific URL.

    :param load: Current load level (decays over time).
    :param last_updated: Last time the load was updated.
    :param queued: Whether this URL is currently in the write queue.
    """
    load: float
    last_updated: float
    queued: bool = ...

class IndexTimestampModel(BaseModel):
    """
    Pydantic model for a timestamp index entry.

    :param timestamp: The timestamp value.
    """
    timestamp: datetime.datetime
    def serialize_timestamp(self, dt: datetime.datetime) -> str:
        """
        Serialize a datetime object to an ISO8601 string in UTC.

        :param dt: The datetime object to serialize.
        :return: The ISO8601 string representation in UTC.
        """
    @classmethod
    def ensure_timezone(cls, data: dict) -> dict:
        """
        Ensure the timestamp has timezone information, defaulting to UTC if none provided.

        Also handles parsing string timestamps.

        :param data: Input data dictionary.
        :return: Validated data dictionary.
        """

class TimestampHelper:
    """
    Helper class for managing timestamp operations with debouncing support.

    Provides debounced writes to prevent cascading updates to the same URL within a specified time window.
    The debounce interval dynamically increases with multiple writes up to a maximum value.

    Note: It is safe to shutdown and restart the TimestampHelper; the writer thread will be restarted automatically.
    """
    timestamp_helper_instance: TimestampHelper | None
    def __init__(self, debounce_interval: float | None = None, debounce_backoff_threshold: int | None = None, debounce_backoff_multiplier: float | None = None, debounce_backoff_max_level: int | None = None) -> None:
        """
        Initialize the TimestampHelper.

        :param debounce_interval: Initial debounce interval in seconds.
        :param debounce_backoff_threshold: Threshold for increasing backoff level.
        :param debounce_backoff_multiplier: Multiplier for increasing the interval.
        :param debounce_backoff_max_level: Maximum backoff level allowed.
        """
    @property
    def debounce_interval(self) -> float:
        """
        Get the current debounce interval in seconds.

        :return: The current debounce interval in seconds.
        """
    @debounce_interval.setter
    def debounce_interval(self, value: float) -> None:
        """
        Set the debounce interval in seconds.

        :param value: The new debounce interval in seconds.
        """
    @property
    def debounce_backoff_multiplier(self) -> float:
        """
        Get the current backoff multiplier.

        :return: The current backoff multiplier.
        """
    @debounce_backoff_multiplier.setter
    def debounce_backoff_multiplier(self, value: float) -> None:
        """
        Set the backoff multiplier.

        :param value: The new backoff multiplier.
        """
    @property
    def debounce_backoff_max_level(self) -> int:
        """
        Get the maximum backoff level.

        :return: The maximum backoff level.
        """
    @debounce_backoff_max_level.setter
    def debounce_backoff_max_level(self, value: int) -> None:
        """
        Set the maximum backoff level.

        :param value: The new maximum backoff level.
        """
    @property
    def debounce_backoff_threshold(self) -> int:
        """
        Get the current backoff threshold.

        :return: The current backoff threshold.
        """
    @debounce_backoff_threshold.setter
    def debounce_backoff_threshold(self, value: int) -> None:
        """
        Set the backoff threshold.

        :param value: The new backoff threshold.
        """
    @classmethod
    def instance(cls) -> TimestampHelper:
        """
        Get the singleton instance of TimestampHelper.

        :return: The singleton TimestampHelper instance.
        """
    @property
    def is_running(self) -> bool:
        """
        Check if the background debounce write thread is running.

        :return: True if the write thread is running, False otherwise.
        """
    def schedule_timestamp_write(self, url: Url) -> None:
        """
        Schedule a timestamp write for the given URL.

        Multiple calls for the same URL are coalesced - only one write will be
        queued at a time, but load accumulates to influence backoff timing.
        """
    def start(self) -> None:
        """
        Start the Timestamp debounce writer thread.

        The write thread starts automatically the first time. After this it must be explicitly started whenever it is
        stopped.

        Note. The writer thread is automatically started if it is stopped unless the disabled_timestamp_writes attribute
        is set.
        """
    def flush(self) -> None:
        """
        Flush all pending writes immediately. This ensures all pending timestamps are written immediately.
        """
    def stop(self) -> None:
        """
        Flush all pending writes and stop the Timestamp debounce writer thread.
        """
    def read_timestamp(self, url: Url) -> datetime.datetime:
        """
        Read a timestamp from the given URL and return it as a datetime object.

        This expects the timestamp content to be in ISO 8601 format with a timezone offset. If no timezone offset is
        provided it will be converted to UTC.

        :param url: The URL to read the timestamp from.
        :return: The timestamp as a datetime object.
        """
    def remove_timestamp(self, url: Url) -> None:
        """
        Remove the timestamp at the given URL.

        This can be used to signal that content has changed and indexing should be re-run. Only updates internal state
        if the delete operation succeeds.

        :param url: URL to remove the timestamp for.
        :raises OSError: If deletion fails.
        """
    def get_written_timestamps(self) -> dict[Url, datetime.datetime]:
        """
        Get all currently written timestamps as a dict with URL as key and timestamp as value.

        :return: Dictionary mapping URLs to their timestamps.
        """
    @contextmanager
    def temporary_debounce_interval(self, interval: float) -> Iterator[None]:
        """
        Context manager that temporarily sets a different debounce interval.

        The original interval is restored when exiting the context, even if an exception occurs. Thread-safe using the
        existing read-write lock.

        :param interval: The temporary debounce interval in seconds to use.
        :raises ValueError: If interval is not positive.
        """
    @contextmanager
    def disabled_timestamp_notifications(self) -> Iterator[None]:
        """
        Context manager that temporarily disables all timestamp notifications.

        Pending writes are processed normally but no new notifications are collected and no writes are scheduled.
        """
    @contextmanager
    def disabled_timestamp_writes(self) -> Iterator[None]:
        """
        Context manager that temporarily disables all timestamp writes.

        Any pending writes are flushed before disabling writes (as a part of the stop operation). New writes will be
        queued but not executed until after exiting the context. Thread-safe using the existing read-write lock.

        Example usage::

            with helper.disabled_timestamp_writes():
                # No timestamps will be written during this block
                ...
        """
    def process_timestamp(self, project_root: Url) -> None:
        """
        Process a timestamp operation for the given project root.

        :param project_root: The root URL of the project.
        """
    def notify_operation(self, url: Url, op: Literal['write', 'delete']) -> None:
        '''
        Handle notification of a file operation.

        :param url: The URL where the operation occurred.
        :param op: The type of operation performed ("write" or "delete").
        '''
