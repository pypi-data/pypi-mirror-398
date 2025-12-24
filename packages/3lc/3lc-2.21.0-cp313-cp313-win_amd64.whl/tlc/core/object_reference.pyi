from _typeshed import Incomplete
from tlc.core.object import Object as Object
from tlc.core.object_registry import ObjectRegistry as ObjectRegistry
from tlc.core.url import Url as Url

class ObjectReference:
    '''Represents a reference to an Object, with optional lazy resolution.

    The `ObjectReference` class is designed to manage references to objects and resolve
    them lazily when requested. It can be initialized from an object, a URL, or a string.
    The class also provides functionalities like type casting and URL management.

    The Url will be stored as a relative Url with respect to the owner_url if provided, otherwise it will be stored as
    given.

    :Example:

    ```python
    my_url = Url("http://example.com/object")
    obj_ref = ObjectReference(my_url)
    actual_object = obj_ref.object
    ```

    :Closing Comments:

    - **Lazy Resolution**: The actual object is only loaded when specifically requested.
    - **Type Safety**: Allows you to cast the object to a specified type when retrieving it.
    '''
    owner_url: Incomplete
    def __init__(self, create_from: str | Url | Object, owner_url: Url | None = None) -> None:
        """Initialize an `ObjectReference`.

        You can initialize the reference with either an object, a URL, or a string.

        :param create_from: The initial value to create the reference from.
        :param owner_url: The URL of the owning object, if any.
        """
    def __bool__(self) -> bool:
        """Check if the object reference is valid.

        Determines whether the reference holds a URL or an actual object.

        :returns: `True` if valid, `False` otherwise.
        """
    def resolve(self) -> bool:
        """Resolve the referenced object.

        Loads the actual object if it is not already loaded. Otherwise, it's a no-op.

        :returns: `True` if the object was resolved, `False` if it was already loaded.
        :raises ValueError: If unable to resolve the reference.
        """
    @property
    def object(self) -> Object:
        """Returns the referenced object

        If not already loaded, this method will first instantiate the object from the Url
        If the resolving fails a ValueError is raised"""
    def object_as(self, object_type: type[_T]) -> _T:
        """Get the referenced object, cast to a specific type.

        :Example:

        ```python
        my_ref = ObjectReference(some_url)
        my_typed_object = my_ref.object_as(SomeType)
        ```

        :param object_type: The type to cast the object to.
        :returns: The object, cast to the specified type.
        :raises AssertionError: If the object's type doesn't match the specified type.
        """
    @property
    def url(self) -> Url:
        """Get the URL of the referenced object.

        Useful for serialization and debugging.

        :returns: The URL of the referenced object.
        """
