from tlc.core.object import Object as Object
from tlc.core.object_type_registry import ObjectTypeRegistry as ObjectTypeRegistry
from tlc.core.schema import Schema as Schema
from tlc.core.url import Url as Url
from typing import Any

class NullObject(Object):
    """A minimal empty object"""
    def __init__(self, url: Url | None = None, created: str | None = None, init_parameters: Any = None) -> None: ...
    def should_include_schema_in_json(self, _: Schema) -> bool: ...
