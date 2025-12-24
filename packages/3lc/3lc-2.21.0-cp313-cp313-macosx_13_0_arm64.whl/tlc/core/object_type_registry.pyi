from _typeshed import Incomplete
from tlc.core.object import Object as Object
from typing import Any, Literal

logger: Incomplete

class NotRegisteredError(Exception):
    """Exception raised when a type or component is not registered."""
    type_name: Incomplete
    message: Incomplete
    def __init__(self, type_name: str) -> None: ...

class MalformedContentError(ValueError):
    """Exception raised when a serialized object does not contain expected attributes."""
    missing_attribute: Incomplete
    message: Incomplete
    def __init__(self, missing_attribute: str) -> None: ...

class ObjectTypeRegistry:
    '''A class which maintains a global list of registered 3LC object types.

    This list is used e.g. when a JSON string containing a \'type\' property needs
    to be mapped to a create_object() method on a particular class.

    Note that the registry also contains abstract types like "Table" in order to
    deduce inheritance and order between types.
    '''
    @staticmethod
    def set_fallback_load_strategy(strategy: Literal['opaque', 'lazy']) -> None:
        '''Set the preferred strategy for loading object types when direct type mapping fails.

        This controls the order in which fallback mechanisms are tried when resolving object types:
          - "lazy": First attempts to load the type through optional imports, then tries opaque table. Lazy loading
            allows the system to fully recognize and use the type, but may be slower to load.
          - "opaque": First attempts to create an opaque table, then tries optional imports. Opaque loading is faster,
            but may not fully recognize and use the type.

        :param strategy: The preferred loading strategy, either "opaque" or "lazy"
        '''
    @staticmethod
    def register_optional_import_for_type(type_name: str, import_path: str) -> None:
        """
        Register an optional import for a type.

        This allows the system to delay importing a type until it's actually needed. When a type is requested during
        loading, the system will import it from the specified path if it hasn't been registered yet.

        :param type_name: The name of the type to register
        :param import_path: The import path to use when the type is requested
        """
    @staticmethod
    def register_object_type(obj_type: type[Object]) -> None:
        """
        Register a 3LC object type (i.e. a class derived from Object) so that it
        can be mapped to a 'type' property found within a JSON structure.

        This way, instances of the class can be instantiated from JSON strings
        as needed.
        """
    @staticmethod
    def get_object_type_from_type_name(type_name: str) -> type[Object] | None:
        """
        Get 3LC object type from type name.

        :param type_name: The type name to look up
        :return: The object type if found, otherwise None
        :raises NotRegisteredError: If the type name is not registered
        """
    @staticmethod
    def print_object_types(line_prefix: str = '') -> None:
        """
        Print all object types. OlaFixme! Print class hierarchy recursively
        """
    @staticmethod
    def is_type_registered(_type_name: str) -> bool:
        """Reports whether a type name is registered in the system

        Only registered types can be instantiated"""
    @staticmethod
    def is_type_derived_from(_type: str, _base_type: str) -> bool:
        """
        Reports whether an object type is derived from another

        Raises if the type strings are not possible to resolve into registered types
        """
    @staticmethod
    def get_object_type_from_content(content: Any) -> type[Object] | None:
        '''Returns the object type for the given content.

        The following logic is applied based on the preferred load order:

        1. First tries to map the contents \'type\' attribute using the registered typename map
        2. Then based on _preferred_load_order:
           - If "lazy": Tries to import the type from the optional import path
           - If "opaque": Tries to infer if the table can be served as an opaque table
        3. Finally tries the other fallback mechanism that wasn\'t preferred

        :param content: A dictionary containing the properties of an object.
        :returns: The object type for the given content.
        '''
