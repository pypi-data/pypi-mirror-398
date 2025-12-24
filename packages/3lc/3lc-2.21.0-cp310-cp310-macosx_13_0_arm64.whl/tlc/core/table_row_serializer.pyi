import abc
from _typeshed import Incomplete
from abc import ABC, abstractmethod
from typing import Any

class TableRowSerializer(ABC, metaclass=abc.ABCMeta):
    """
    The base class for table row serializers.
    """
    internal_name: Incomplete
    def __init__(self, internal_name: str) -> None: ...
    @abstractmethod
    def internal_serialize(self, table: Any) -> bytes:
        """Serialize a table to a particular binary format"""
