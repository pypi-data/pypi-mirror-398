from _typeshed import Incomplete
from collections.abc import Sequence
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.schema import DictValue as DictValue, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from tlc.core.url_adapters import ApiUrlAdapter as ApiUrlAdapter
from tlc.core.utils.telemetry import Telemetry as Telemetry
from typing import Any

logger: Incomplete

class Configuration(MutableObject):
    """
    3LC runtime configuration.

    This singleton object contains all runtime configuration settings for this
    instance of 3LC, including

    - Current-user information
    - Network access tokens
    - Cache settings
    - Other settings
    - ...
    """
    configuration_instance: Configuration | None
    project_root_url: Incomplete
    project_scan_urls: Incomplete
    extra_table_scan_urls: Incomplete
    extra_run_scan_urls: Incomplete
    sentry_dashboard_config: Incomplete
    def __init__(self, url: Url | None = None, project_root_url: Url | str | None = None, project_scan_urls: Sequence[Url | str | dict] | None = None, extra_table_scan_urls: Sequence[Url | str | dict] | None = None, extra_run_scan_urls: Sequence[Url | str | dict] | None = None, aliases: dict[str, str] | None = None, created: str | None = None, last_modified: str | None = None, init_parameters: Any = None) -> None: ...
    @property
    def aliases(self) -> dict[str, str]:
        """Return the URL aliases."""
    @staticmethod
    def instance() -> Configuration:
        """
        Returns the singleton Configuration object
        """
    def ensure_dependent_properties(self) -> None:
        """Configuration is dependent on the ConfigIndexingTable, ensure they are up to date."""
