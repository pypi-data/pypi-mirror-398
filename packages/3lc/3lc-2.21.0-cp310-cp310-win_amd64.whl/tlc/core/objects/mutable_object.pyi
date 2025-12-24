import datetime
from _typeshed import Incomplete
from collections.abc import Mapping
from tlc.core.object import Object as Object
from tlc.core.schema import DatetimeStringValue as DatetimeStringValue, Schema as Schema
from tlc.core.url import Url as Url
from tlc.utils.datetime_helper import DateTimeHelper as DateTimeHelper
from typing import Any

logger: Incomplete

class MutableObject(Object):
    '''Base class for objects that can be mutated.

    MutableObject properties:

    \'last_modified\': The time when this object was last modified.

    The MutableObject have designated update_attribute/s methods that are meant to be used to modify the object\'s
    attributes. Using these function to modify objects makes sure that the objects\' internal state are updated
    correctly, e.g. sets the \'last_modified\' timestamp.

    Directly modifying MutableObject (public) attributes from the outside using `mutable_obj.attr = value` or
    `setattr(mutable_obj, "attr", value)` is not recommended. But, if object attributes have to be set directly, make
    sure to call the `update_internal_state` to signal the update.

    '''
    last_modified: str
    def __init__(self, url: Url | None = None, created: str | None = None, last_modified: str | None = None, init_parameters: Any = None) -> None: ...
    def update_internal_state(self, persist: bool = True) -> None:
        """Updates the internal state of the object.

        Override this method to update the internal state of the object whenever attributes have been changed. This
        method is called by the `update_attribute/s`
        """
    def update_attribute(self, attr_name: str, value: Any) -> None:
        """Updates the given attribute with the given value.

        This method will only allow modification of attributes that are defined in the object's schema and are
        writeable. If the object schema is has not yet been evaluated, this method will do so. If the object does not
        have a Schema a ValueError will be raised.

        If the attribute is modified the object's 'last_modified' timestamp is updated. The internal state of the object
        is also updated by calling the `_update_internal_state` method.

        :param attr_name: The name of the attribute to update.
        :param value: The value to set.
        :returns: True if the object was changed, False otherwise.
        :raises ValueError: if the schema is not set, or attribute name is unknown."""
    def update_attributes(self, attribute_dict: Mapping[str, object]) -> None:
        """Updates the object with the given attribute_name,value pairs.

        This method will only allow modification of attributes that are defined in the object's schema and are
        writeable. If the object schema is has not yet been evaluated, this method will do so. If the object does not
        have a Schema a ValueError will be raised.

        If the attribute is modified the object's 'last_modified' timestamp is updated. The internal state of the object
        is also updated by calling the `update_internal_state` method.

        :param attr_name: The name of the attribute to update.
        :param value: The value to set.
        :returns: True if the object was changed, False otherwise.
        :raises ValueError: if the schema is not set, or attribute name is unknown."""
    def update(self, init_parameters: Mapping[str, object]) -> None: ...
    @staticmethod
    def add_last_modified_property_to_schema(schema: Schema, description: str) -> None:
        """Add the 'last_modified' property to this schema"""
    def to_json(self, init_level: int = 0) -> str:
        """
        Returns a JSON representation of this object. This will be sufficient to recreate
        a fully functioning clone of the object at a later time.

        Note that for brevity, properties with default values are not written to the string.
        """
    def touch_last_modified(self) -> None:
        """Updates the last_modified timestamp to the current UTC time"""
    def is_stale(self, timestamp: datetime.datetime | str | None, epsilon: float = 0.0) -> bool:
        """Indicates whether this object is stale compared to the given timestamp (using `last_modified` property).

        The function compares the object's `last_modified` timestamp with the provided timestamp. If the difference
        exceeds the provided epsilon value, the object is considered stale.

        :param other_timestamp: The timestamp against which to check staleness. Can be None.
        :param epsilon: The tolerance in seconds for staleness. If the difference between the object's timestamp and the
            provided timestamp exceeds this value, the object is considered stale. Defaults to 0.0s.
        :returns: True if the object is stale, False otherwise.

        :raises ValueError: if the timestamp is invalid.
        """
