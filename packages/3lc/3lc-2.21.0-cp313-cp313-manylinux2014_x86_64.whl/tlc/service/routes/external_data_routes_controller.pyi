from _typeshed import Incomplete
from litestar.connection.request import Request as Request
from litestar.controller import Controller
from litestar.response.base import Response
from tlc.core import Table as Table
from tlc.core.object import Object as Object
from tlc.core.url import Url as Url
from tlc.core.url_adapter import IfExistsOption as IfExistsOption
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlc.service.routes.external_data_transcoders import get_transcoder as get_transcoder

logger: Incomplete

def resolve_cache_timeout() -> int: ...

class ExternalDataRoutesController(Controller):
    """Controller for all external data-related routes"""
    path: str
    cache_time_out: Incomplete
    async def get_encoded_url(self, encoded_url: str) -> bytes: ...
    async def post_encoded_url(self, request: Request, owner_url: str, base_name: str, extension: str) -> Response:
        """Write a new file with given binary contents.

        :param request: The request object.
        :param owner_url: The URL of the tlc Object that owns the file. Currently only support Table owners, data will
            be written in the table's bulk data folder.
        :param base_name: The base name of the file or folder to be created. Used to provide more context to the
            filename.
        :param extension: The extension of the file.

        :returns: A response with a 201 status code and a Location header pointing to the newly created file.
        """
    async def get_encoded_url_binary_contents(self, encoded_url: str, format: str) -> Response: ...
