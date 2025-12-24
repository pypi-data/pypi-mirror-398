import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from datetime import timedelta
from sentry_sdk.integrations import Integration
from sentry_sdk.tracing import Span as Span
from tlc.core.utils.track_project_metadata import compute_project_usage_metadata as compute_project_usage_metadata, get_project_usage_metadata as get_project_usage_metadata
from tlcsaas.sentry_config import SentryConfiguration as SentryConfiguration
from typing import Any, Callable, Literal

logger: Incomplete

class JupyterExcepthookIntegration(Integration):
    """Hook into Jupyter's excepthook to capture unhandled exceptions so that they get reported to Sentry."""
    identifier: str
    @staticmethod
    def setup_once() -> None: ...

TELEMETRY_SPAN_OP_DEFAULT: str

class Telemetry:
    """Telemetry class for 3LC.

    This class is responsible for initializing the telemetry system for 3LC.
    """
    telemetry_instance: Telemetry | None
    def __init__(self) -> None: ...
    @staticmethod
    def instance() -> Telemetry:
        """Get the telemetry instance."""
    @staticmethod
    def get_sentry_environment() -> str:
        '''Get the Sentry environment.

        This method uses various heuristics to determine the environment in which the code is running.

        1. If the TLC_SENTRY_ENVIRONMENT environment variable is set, it will take precedence over the other logic.
        2. If the tlc module is installed from a wheel, the environment will be set to "production", unless the user is
           an internal 3LC user, in which case it will be set to "development".
        3. If neither of those conditions is met (i.e. TLC_SENTRY_ENVIRONMENT is not set and we are running from
           source), the environment will be set to "local".
        '''
    @staticmethod
    def get_sentry_config() -> SentryConfiguration: ...
    @staticmethod
    def get_sentry_dashboard_config() -> dict: ...
    @property
    def is_enabled(self) -> bool: ...
    def should_capture_messages(self, is_include_object_service: bool = True) -> bool: ...
    def capture_message(self, message_text: str, message_tags: dict[str, Any] | None = None, message_extras: dict[str, Any] | None = None, level: Literal['fatal', 'critical', 'error', 'warning', 'info', 'debug'] = 'info', include_stack_trace: bool = False) -> None: ...
    def capture_instantaneous_span(self, *, span_name: str, span_op: str = ..., span_tags: dict[str, Any] | None = None, span_data: dict[str, Any] | None = None, is_create_transaction_if_none: bool = False) -> str: ...
    def capture_instantaneous_transaction_span(self, *, span_name: str, span_op: str = ..., span_tags: dict[str, Any] | None = None, span_data: dict[str, Any] | None = None, trace_id: str = '') -> str: ...
    @staticmethod
    def get_stack_trace() -> list[str]: ...

class BaseTelemetrySpan(ABC, metaclass=abc.ABCMeta):
    """Base class for telemetry spans that defines the common interface and shared functionality."""
    span_name: Incomplete
    is_include_object_service: Incomplete
    is_include_exit_on_error: Incomplete
    get_enter_tags: Incomplete
    get_enter_data: Incomplete
    get_exit_tags: Incomplete
    get_exit_data: Incomplete
    def __init__(self, span_name: str, *, is_include_exit_on_error: bool = False, is_include_object_service: bool = False, get_enter_tags: Callable[[], dict[str, Any]] | None = None, get_enter_data: Callable[[], dict[str, Any]] | None = None, get_exit_tags: Callable[[], dict[str, Any]] | None = None, get_exit_data: Callable[[], dict[str, Any]] | None = None) -> None: ...
    @abstractmethod
    def on_span_start(self, tags: dict[str, Any], data: dict[str, Any]) -> None:
        """Called when the span starts. Implementations should set up the telemetry object and record initial state."""
    @abstractmethod
    def on_span_stop(self, tags: dict[str, Any], data: dict[str, Any]) -> None:
        """Called when the span stops. Implementations should record final state and clean up the telemetry object."""
    def __enter__(self) -> BaseTelemetrySpan:
        """Start tracking with telemetry."""
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Stop tracking with telemetry."""

class TelemetrySpan(BaseTelemetrySpan):
    """A telemetry span that assumes a top-level transaction is already in place"""
    span_op: Incomplete
    span: Span | None
    def __init__(self, span_name: str, *, span_op: str = ..., is_include_exit_on_error: bool = False, is_include_object_service: bool = False, get_enter_tags: Callable[[], dict[str, Any]] | None = None, get_enter_data: Callable[[], dict[str, Any]] | None = None, get_exit_tags: Callable[[], dict[str, Any]] | None = None, get_exit_data: Callable[[], dict[str, Any]] | None = None) -> None: ...
    def create_span(self) -> Span: ...
    def on_span_start(self, tags: dict[str, Any], data: dict[str, Any]) -> None: ...
    def on_span_stop(self, tags: dict[str, Any], data: dict[str, Any]) -> None: ...
    def __enter__(self) -> TelemetrySpan: ...
    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None: ...
    def capture_child_span(self, span_name: str, span_op: str = ..., span_tags: dict[str, Any] | None = None, span_data: dict[str, Any] | None = None) -> None: ...

class TelemetryTransaction(TelemetrySpan):
    """A top-level telemetry transaction span."""
    def __init__(self, transaction_name: str, *, transaction_op: str = ..., is_include_exit_on_error: bool = False, is_include_object_service: bool = False, get_enter_tags: Callable[[], dict[str, Any]] | None = None, get_enter_data: Callable[[], dict[str, Any]] | None = None, get_exit_tags: Callable[[], dict[str, Any]] | None = None, get_exit_data: Callable[[], dict[str, Any]] | None = None) -> None: ...
    def create_span(self) -> Span: ...

class MultiTransactionTelemetrySpan(BaseTelemetrySpan):
    """
    A telemetry span for long-running operations that you do not want to wait to finish before getting any telemetry.
    Sends an instantaneous transaction at start and stop and at a regular heartbeat interval.
    """
    session_id: Incomplete
    span_op: Incomplete
    get_heartbeat_tags: Incomplete
    get_heartbeat_data: Incomplete
    start_time: Incomplete
    trigger_time: Incomplete
    def __init__(self, span_name: str, *, span_op: str = ..., is_include_exit_on_error: bool = False, is_include_object_service: bool = False, get_enter_tags: Callable[[], dict[str, Any]] | None = None, get_enter_data: Callable[[], dict[str, Any]] | None = None, get_exit_tags: Callable[[], dict[str, Any]] | None = None, get_exit_data: Callable[[], dict[str, Any]] | None = None, get_heartbeat_tags: Callable[[], dict[str, Any]] | None = None, get_heartbeat_data: Callable[[], dict[str, Any]] | None = None, heartbeat_interval: timedelta | None = None, start_message: str | None = None, stop_message: str | None = None, heartbeat_message: str | None = None) -> None: ...
    def __enter__(self) -> MultiTransactionTelemetrySpan: ...
    def on_span_start(self, tags: dict[str, Any], data: dict[str, Any]) -> None: ...
    def on_span_stop(self, tags: dict[str, Any], data: dict[str, Any]) -> None: ...
    async def consider_heartbeat_message(self) -> None:
        """Send a heartbeat message with current state if no interval is specified or if the interval has elapsed."""

class ObjectServiceTelemetrySpan(MultiTransactionTelemetrySpan):
    def __init__(self, *, tui: bool, with_public_examples: bool, ngrok: bool) -> None: ...
