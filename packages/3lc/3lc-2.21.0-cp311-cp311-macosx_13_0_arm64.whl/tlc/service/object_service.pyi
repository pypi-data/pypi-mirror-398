from _typeshed import Incomplete
from litestar.app import Litestar
from litestar.connection.request import Request as Request
from litestar.middleware.logging import LoggingMiddleware, LoggingMiddlewareConfig
from litestar.openapi.spec import SecurityRequirement as SecurityRequirement
from litestar.response.base import Response
from litestar.types import ASGIApp as ASGIApp, Receive as Receive, Scope as Scope
from litestar.types.callable_types import LifespanHook as LifespanHook
from litestar.types.composite_types import Middleware as Middleware
from pydantic import BaseModel
from tlc import __git_revision__ as __git_revision__, __version__ as __version__
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.objects.tables.system_tables.indexing_tables.config_indexing_table import ConfigIndexingTable as ConfigIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.run_indexing_table import RunIndexingTable as RunIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.table_indexing_table import TableIndexingTable as TableIndexingTable
from tlc.core.objects.tables.system_tables.log_table import LogTable as LogTable
from tlc.core.objects.tables.system_tables.timestamp_helper import TimestampHelper as TimestampHelper
from tlc.core.url import UrlAliasRegistry as UrlAliasRegistry
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.core.utils.telemetry import Telemetry as Telemetry
from tlc.core.utils.track_project_metadata import compute_project_usage_metadata as compute_project_usage_metadata
from tlc.service.authentication import ActivateJwtOnApiKeyMiddleware as ActivateJwtOnApiKeyMiddleware, JwtAuthenticationMiddleware as JwtAuthenticationMiddleware, TimestampHmacAuthenticationMiddleware as TimestampHmacAuthenticationMiddleware, TimestampSkewException as TimestampSkewException
from tlc.service.lru_cache_store import LRUCacheStore as LRUCacheStore, LRUCacheStoreConfig as LRUCacheStoreConfig
from tlc.service.routes.external_data_routes_controller import ExternalDataRoutesController as ExternalDataRoutesController
from tlc.service.routes.object_routes_controller import ObjectRoutesController as ObjectRoutesController
from tlc.service.routes.settings_routes_controller import SettingsRoutesController as SettingsRoutesController
from tlc.service.watch_manager import is_watch_enabled as is_watch_enabled, start_watch_subprocess as start_watch_subprocess, stop_watch_subprocess as stop_watch_subprocess
from tlccli.subcommands.ngrok_helper import NGrokHelper
from tlcsaas.transaction import InsufficientCredits
from typing import Any, TypeVar

logger: Incomplete

class LitestarStateConstants:
    """Constants for the Litestar state."""
    HOST_IP: str
    OBJECT_SERVICE_RUNNING_URLS: str
    NGROK_OBJECT_SERVICE_URL: str

def internal_server_error_handler(request: Request, exception: Exception) -> Response:
    """Catch-all for application errors."""
def insufficient_credits_handler(request: Request, exception: InsufficientCredits) -> Response:
    """Handler for insufficient credits."""
def timestamp_skew_handler(request: Request, exception: TimestampSkewException) -> Response:
    """Handler for timestamp skew."""
def get_ip_addresses() -> list[str]: ...
def get_running_urls() -> list[str]: ...

profiler: Incomplete

def format_yaml_for_logging(data: dict | list, indent: int = 4) -> str: ...
def open_in_web_browser(url: str) -> None: ...
def open_dashboard_in_web_browser(app: Litestar) -> None: ...
async def startup(app: Litestar) -> None:
    """Setup HTTP client for connecting to 3LC Data Service"""
async def shutdown(app: Litestar) -> None:
    """Perform any required cleanup before terminating the application"""
async def root() -> Response:
    """Root endpoint of the service"""
async def live() -> Response:
    """Endpoint for checking if the service is running."""

class ObjectServiceFeatures(BaseModel):
    post_external_data: bool
    post_objects_multi_part: bool

class ObjectServiceUserInfo(BaseModel):
    user_id: str
    tenant_id: str
    user_full_name: str
    user_email: str
    tenant_name: str

class DashboardAnnotations(BaseModel):
    banner_icon_url: str
    banner_background_color: str
    banner_message: str
    title_message: str

def get_status() -> dict[str, Any]:
    """Returns status of the service"""

last_lru_stats: dict[str, Any] | None

def get_last_lru_stats() -> dict[str, Any] | None: ...
async def status(request: Request) -> dict[str, Any]:
    """Returns status of the service"""

class TLCCustomLoggingMiddleware(LoggingMiddleware):
    """Custom middleware to log object service requests and responses.

    Logs request and response data to loglevel.INFO, together with the time it takes to complete the request.
    """
    def __init__(self, app: ASGIApp, config: LoggingMiddlewareConfig) -> None: ...
    async def log_request(self, scope: Scope, receive: Receive) -> None:
        """Record the start time and log the request data."""
    def log_response(self, scope: Scope) -> None:
        """Measure elapsed time and log the response data."""
    def log_message(self, values: dict[str, Any]) -> None:
        """Log a message.

        This is a copy of the superclass' method, with special case handling of the /status endpoint, and url decoding
        of the path.

        :param values: Extract values to log.
        :returns: None
        """

class NGrokOutputAdaptor:
    """Helper class to format output from NGrokHelper for the Object Service."""
    ngrok_helper: Incomplete
    role: Incomplete
    def __init__(self, role: str, ngrok_helper: NGrokHelper) -> None: ...
    async def output_public_url(self, app: Litestar) -> None: ...
T = TypeVar('T')

def create_litestar_app(host: str, port: int, use_ngrok: bool, dashboard: bool = False, after_startup_handler: list[LifespanHook] | LifespanHook | None = None, after_shutdown_handler: list[LifespanHook] | LifespanHook | None = None) -> Litestar: ...
