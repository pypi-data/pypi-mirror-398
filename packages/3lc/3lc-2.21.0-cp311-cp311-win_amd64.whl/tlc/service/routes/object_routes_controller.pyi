import datetime
import pydantic
from _typeshed import Incomplete
from collections.abc import Generator
from contextlib import contextmanager
from litestar.connection.request import Request as Request
from litestar.controller import Controller
from litestar.params import Parameter as Parameter
from litestar.response.base import Response
from tlc.core import ObjectRegistry as ObjectRegistry
from tlc.core.json_helper import JsonHelper as JsonHelper
from tlc.core.object import Object as Object
from tlc.core.object_type_registry import MalformedContentError as MalformedContentError, NotRegisteredError as NotRegisteredError
from tlc.core.objects.mutable_object import MutableObject as MutableObject
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.objects.table import Table as Table
from tlc.core.objects.tables.system_tables.indexing_table import IndexingTable as IndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.config_indexing_table import ConfigIndexingTable as ConfigIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.run_indexing_table import RunIndexingTable as RunIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.table_indexing_table import TableIndexingTable as TableIndexingTable
from tlc.core.objects.tables.system_tables.log_table import LogTable as LogTable
from tlc.core.url import Url as Url
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from typing import Annotated, Any, ClassVar, Literal

logger: Incomplete

class TLCObject(pydantic.BaseModel):
    """In-flight representation of a TLCObject."""
    type: str
    url: str | None
    model_config: Incomplete

class TLCPatchOptions(pydantic.BaseModel):
    """TLC patch request."""
    delete_old_url: bool
    model_config: Incomplete

class TLCPatchRequest(pydantic.BaseModel):
    """In-flight representation of a patch request for a TLCObject."""
    patch_object: TLCObject
    patch_options: TLCPatchOptions
    model_config: Incomplete

class ReindexRequest(pydantic.BaseModel):
    '''Request model for re-indexing operations.

    :param force: Whether to force re-indexing to disregard the state of the current index timestamp files.
    :param types: The types of objects to reindex. Defaults to "all".
    '''
    force: bool
    types: list[Literal['run', 'table', 'config', 'all']]
    model_config: Incomplete

class RollbackDeleteContext:
    """A context manager for rollback object creation without interfering with InsufficientCredits."""
    def __init__(self, url: Url) -> None: ...
    def rollback(self) -> None: ...
    def __enter__(self) -> RollbackDeleteContext: ...
    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Literal[False]:
        """Exit the context, performing rollback if not committed and handling exceptions."""

class MultipartData:
    """Multipart data."""
    data_parts: dict[int, bytes]
    total_parts: int
    timestamp: datetime.datetime
    def __init__(self, total_parts: int) -> None: ...
    @property
    def should_dispose(self) -> bool:
        """Check if this multipart data should be disposed."""
    def mark_for_disposal(self) -> None:
        """Mark this multipart data for disposal."""
    def add_data(self, data: bytes, part_number: int, total_parts: int) -> None:
        """Add a data part and check if accepted or rejected.

        :param data: The data bytes for this part
        :param part_number: The part number (0-indexed)
        :param total_parts: The total number of parts expected
        """
    def is_complete(self) -> bool:
        """Check if all parts have been received."""
    def get_data(self) -> bytes:
        """Get the complete request body as a bytes object.

        :raises ValueError: If the multipart request is not complete.
        :returns: The complete request body as bytes.
        """

class ObjectRoutesController(Controller):
    """Controller for all object-related routes"""
    path: str
    dict_to_multipart_data: ClassVar[dict[str, MultipartData]]
    @classmethod
    def cleanup_stale_multipart_data(cls, max_age_seconds: int = 3600, now: datetime.datetime | None = None) -> int:
        """Clean up stale multipart data that hasn't been updated recently.

        :param max_age_seconds: Maximum age in seconds for incomplete multipart uploads (default: 1 hour)
        :param now: Current time to use for age calculation. If None, uses datetime.datetime.now(datetime.timezone.utc)
        :returns: Number of stale entries removed
        """
    @contextmanager
    def multipart_resource(self, multipart_id: str, total_parts: int) -> Generator[MultipartData, None]:
        """Context manager for accessing multipart data.

        :param multipart_id: The multipart request ID
        :param total_parts: Total number of parts expected for this multipart request
        :returns: Generator that yields the multipart data and cleans up if the multipart is complete
        """
    async def get_encoded_url(self, encoded_url: str, request: Request) -> Response: ...
    async def get_encoded_url_rows(self, encoded_url: str, attribute: str, request: Request) -> Response[bytes]: ...
    async def list_urls(self) -> list[str]:
        """Return all the objects.

        Returns:
            list[Any]: List of the URLs of all the objects.
        """
    async def request_reindex(self, data: ReindexRequest) -> Response:
        """Request a reindex operation.

        :param data: The reindex request parameters.
        :returns: Response with status message.
        """
    async def new_object(self, data: TLCObject) -> Response:
        """Create a new object.

        :param data: Object to be created
        :returns: Empty response. URL of the created object will be in the 'Location' field of the response headers.
        """
    async def new_object_multipart(self, body: bytes, upload_id: Annotated[str, None], upload_part_index: Annotated[int, None], upload_part_count: Annotated[int, None]) -> Response:
        """Create a new object from a multipart request.

        :param body: The multipart request body containing the JSON data part
        :param multipart_id: The multipart request ID (from header)
        :param multipart_part_number: The part number (0-indexed, from header)
        :param multipart_total_parts: The total number of parts expected (from header)
        :returns: Empty response. URL of the created object will be in the 'Location' field of the final
            response header.
        """
    async def delete_object(self, encoded_url: str) -> None:
        """Delete an object.

        :param encoded_url: URL of the object to be deleted.
        :raises: HTTPException if no object can be found at the URL.
        """
    async def update_object(self, encoded_url: str, data: TLCPatchRequest) -> Response:
        """Update the attributes of an object.


        Raises:
            HTTPException: If the object type of `obj_in` does not match the
            type of the object at `object_url`.
        """
