from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.objects.table import Table as Table
from tlc.core.url import Url as Url

class TableFromTFRecordSet(Table):
    """A table populated from a TensorFlow RecordSet object"""
    def __init__(self, *, url: Url | None = None) -> None: ...
    def __len__(self) -> int:
        """Get the number of rows in this table"""
