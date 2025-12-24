from _typeshed import Incomplete
from tlc.core.builtins.constants.string_roles import STRING_ROLE_DATETIME as STRING_ROLE_DATETIME, STRING_ROLE_VERSION as STRING_ROLE_VERSION
from tlc.core.json_helper import JsonHelper as JsonHelper
from tlc.core.project_context import ProjectContext as ProjectContext
from tlc.core.schema import BoolValue as BoolValue, DictValue as DictValue, ObjectTypeStringValue as ObjectTypeStringValue, Schema as Schema, StringValue as StringValue, UrlStringValue as UrlStringValue
from tlc.core.serialization_version_helper import SerializationVersionHelper as SerializationVersionHelper
from tlc.core.transaction_closer import TransactionCloser as TransactionCloser
from tlc.core.url import Scheme as Scheme, Url as Url
from tlc.core.url_adapter import IfExistsOption as IfExistsOption
from tlc.core.url_adapter_registry import UrlAdapterRegistry as UrlAdapterRegistry
from tlcsaas.transaction import Transaction as Transaction
from typing import Any, Literal, final

logger: Incomplete

class Object:
    '''The base class for all 3LC objects.

    :ivar type: Which class this object is (used by factory method to instantiate
    the correct class during JSON deserialization)

    :ivar url: The URL which this object instance was deserialized FROM, or
    should be serialized TO. Note that this value is NOT written to JSON, since the JSON representation
    could potentially be moved around (as in e.g. a file being moved
    to another folder).

    :ivar created: The time when this object was first created.

    :ivar schema: A property describing the layout of this object. Note that this
    value should NOT be written to JSON, except for objects where
    recreating the schema would be a "heavy" operation. This means, in practice, that the \'schema\' is only ever written
    to JSON for Table objects, and only after they have determined the
    immutable schema for their \'rows\' property.

    :ivar serialization_version: The serialization version of the object.
    '''
    serialization_version: str
    type: str
    created: str
    is_url_writable: Incomplete
    schema: Schema
    transaction_id: str
    def __init__(self, url: Url | None = None, created: str | None = None, init_parameters: Any = None) -> None:
        """
        :param url: The URL of the object.
        :param created: The creation time of the object.
        :param init_parameters: A dictionary containing the initial values of the object's properties.
        """
    @property
    def url(self) -> Url:
        """The URL which this object instance was deserialized from, or should be serialized to."""
    @property
    def root(self) -> Url | None:
        """The root URL of the object, if set.

        This is a transient property that is not serialized.

        :return: The root URL of the object, or None if not set.
        """
    def initial_value(self, property_name: str, new_value: Any, default_value: Any = None) -> Any:
        """A helper method for getting the initial value of a property.

        Returns self.property_name if it exists, or the provided new value if not None else the default_value. This
        pattern allows all creation of new objects to be done via the constructor.

        :param property_name: The name of the property to get the initial value for.
        :param new_value: The value to return if self.property_name is not set.
        :param default_value: The value to return if self.property_name is not set and new_value is None.

        :return: The initial value of the property.
        """
    @final
    def ensure_minimal_schema(self) -> None:
        """Make sure the schema is populated with the minimal properties."""
    def ensure_complete_schema(self) -> None:
        """Make sure the schema is populated with all properties."""
    def ensure_dependent_properties(self) -> None:
        """Make sure dependent properties are populated

        This method must set all properties required to achieve the 'fully defined' state of an object.

        For example: `Table.row_count` is initially set to `UNKNOWN_ROW_COUNT` (-1) to indicate that it is not (yet)
        known, after a call to prepare_data_production it will be set to the correct value.

        Override in subclasses to ensure the required dependent properties are populated
        """
    @final
    def ensure_fully_defined(self) -> None:
        """Make sure the internal state of the object is fully defined.

        For most objects, this simply amounts to populating the 'schema' property
        according to the properties which are directly present within the class.

        For Table objects this also means making sure the 'schema.rows' sub-schema defines the layout of table
        rows if and when they will be produced

        To ensure that data is ready and dependent properties are populated, call ensure_dependent_properties.
        """
    def write_to_url(self, force: bool = False) -> Url:
        """Writes this object to its URL.

        :param force: Whether to overwrite the object if it already exists.

        :return: The URL where the object was written.
        """
    @staticmethod
    def add_object_created_property_to_schema(schema: Schema) -> None:
        """Add the 'created' property to the provided schema.

        :param schema: The schema to add the property to.
        """
    @staticmethod
    def add_object_url_property_to_schema(schema: Schema, url_string_icon: str = '') -> None:
        """Add the 'url' property to the provided schema.

        :param schema: The schema to add the property to.
        :param url_string_icon: The icon to display next to the URL string.
        """
    @staticmethod
    def add_is_url_writable_property_to_schema(schema: Schema) -> None:
        """
        Add the 'is_url_writable' property to the provided schema.

        :param schema: The schema to add the property to.
        """
    def should_include_schema_in_json(self, _schema: Schema) -> bool:
        """Indicate whether the schema property of this object should be included when
        serializing to JSON

        :param _schema: The schema of the object. This is passed in to allow subclasses to
        make decisions based on the schema of the object, but it is not used
        in the base implementation.
        """
    def to_json(self, init_level: int = 1) -> str:
        """Return a JSON representation of this object.

        This will be sufficient to recreate
        a fully functioning clone of the object at a later time.

        Note that for brevity, properties with default values are not written to the string.

        :param init_level: The level of initialization to use when serializing the object.
            1: Minimal schema
            2: Complete schema
            3: Fully defined object

        :return: A JSON representation of this object.
        """
    def copy(self, *, destination_url: Url | None = None, if_exists: Literal['raise', 'rename', 'overwrite'] = 'raise') -> Object:
        """Return a copy of this object, with the specified URL.

        :param destination_url: The url to write the copy to. If not provided, a new url will be generated based on the
            objects own url.
        :param if_exists: How to handle the case where the destination URL already exists.

        :returns: A copy of this object.
        """
    def delete(self) -> None:
        '''Deletes this object from storage.

        This method permanently removes the object from storage by deleting the underlying files or objects that the
        object\'s URL points to. `Object.url` will no longer be valid after this operation.

        :Example:

        ```python
        table = Table.from_dict({"a": [1, 2, 3]})
        table.write_to_url() # persist to storage
        ...
        table.delete() # delete the backing files and objects
        ```

        To delete an object by URL without loading it first, use:
          - `Url("path/to/object").delete()`

        Note: This is different from Python\'s `del` operator - `del obj` only removes the variable name, while
        `obj.delete()` removes the object from storage (and keeps the variable name).
        '''
    def is_stale(self, timestamp: str | None, epsilon: float = 0.0) -> bool:
        """
        Indicate whether this object is stale compared to a given timestamp.

        The base implementation never considers an object stale.
        :param timestamp: The timestamp against which to check staleness. Can be None.
        :param epsilon: The tolerance in seconds for staleness. If the difference between
                        the object's timestamp and the provided timestamp exceeds this value,
                        the object is considered stale. Defaults to 0.0s.
        :returns: True if the object is stale, False otherwise.

        :raises ValueError: if the timestamp is invalid.
        """
    def absolute_url_from_relative(self, input_url: Url) -> Url:
        """Convert a relative URL to be absolute, given the URL of this object.

        :param input_url: The relative URL to convert.

        :return: The absolute URL.
        """
    def relative_url_from_absolute(self, input_url: Url) -> Url:
        """Convert an absolute URL to be relative, given the URL of this object.

        :param input_url: The absolute URL to convert.

        :return: The relative URL.
        """
    @classmethod
    def type_name(cls) -> str:
        """The type name of the class, used to resolve factory methods"""
    @classmethod
    def from_url(cls, url: Url | str) -> Object:
        """Create an Object from a URL.

        :param url: The URL of the object.

        :return: The object.
        """
