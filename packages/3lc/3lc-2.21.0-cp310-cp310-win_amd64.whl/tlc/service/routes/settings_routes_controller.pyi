from _typeshed import Incomplete
from litestar.connection.request import Request as Request
from litestar.controller import Controller
from litestar.response.base import Response

logger: Incomplete

class SettingsRoutesController(Controller):
    """Controller for all settings-related routes"""
    path: str
    async def get_settings_key_value(self, settings_scope: str, settings_key: str) -> Response: ...
    async def put_settings_key_value(self, request: Request, settings_scope: str, settings_key: str) -> Response:
        """Create or update the value for a setting by key.

        :param request: The request object.
        :param settings_scope: The scope of the setting.
        :param settings_key: The key for the setting.
        """
    async def delete_settings_key_value(self, settings_scope: str, settings_key: str) -> None: ...
