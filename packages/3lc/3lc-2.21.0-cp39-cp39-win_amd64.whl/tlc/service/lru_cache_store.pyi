from _typeshed import Incomplete
from datetime import timedelta
from litestar.stores.base import Store
from pydantic import BaseModel

logger: Incomplete

class LRUCacheStoreConfig(BaseModel):
    """LRUCache backend configuration."""
    max_entries: int
    max_memory_in_bytes: int
    time_out_in_seconds: float

class LRUCacheStore(Store):
    """In-memory LRU cache backend."""
    def __init__(self, config: LRUCacheStoreConfig) -> None:
        """Initialize ``LRUCacheBackend``"""
    def stats(self) -> dict[str, int]: ...
    async def get(self, key: str, renew_for: int | timedelta | None = None) -> bytes | None: ...
    async def set(self, key: str, value: str | bytes, expires_in: int | timedelta | None = None) -> None: ...
    async def delete(self, key: str) -> None: ...
    async def delete_all(self) -> None: ...
    async def exists(self, key: str) -> bool: ...
    async def expires_in(self, key: str) -> int | None:
        """Get the time in seconds ``key`` expires in. If no such ``key`` exists or no
        expiry time was set, return ``None``.
        """
