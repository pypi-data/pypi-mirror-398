from collections.abc import Hashable
from typing import Generic, TypeVar

T = TypeVar('T', bound=Hashable)

class _ValueMapBuilder(Generic[T]):
    '''
    Build a stable, contiguous mapping from values to integer ids during a scan,
    then finalize to retrieve both the forward and reverse mappings.

    The first time a value is seen it is assigned the next integer id, starting at 0.
    Subsequent occurrences return the same id. After finalization, no new values may be added.

    :Example:
    ```python
    b = _ValueMapBuilder[str]()
    b("cat"), b("dog"), b("cat")
    # (0, 1, 0)
    fwd, rev = b.finalize()
    fwd["dog"], rev[0]
    # (1, "cat")
    ```
    '''
    def __init__(self) -> None:
        """
        Initialize an empty builder.
        """
    def __call__(self, value: T) -> int:
        """
        Add a value if unseen and return its stable integer id.

        :param value: The value to assign or lookup. Must be hashable.
        :returns: The integer id for the value.
        :raises RuntimeError: If called with a new value after finalization.
        """
    def get(self, value: T) -> int | None:
        """
        Get the id for a value without inserting.

        :param value: The value to lookup.
        :returns: The integer id if present, else None.
        """
    def finalize(self) -> tuple[dict[T, int], dict[int, T]]:
        """
        Finalize and return both forward and reverse mappings.

        - Forward mapping: value -> int (as a dict copy).
        - Reverse mapping: int -> value (as an immutable tuple).

        After this call, the builder is frozen and will not accept new values.

        :returns: A tuple of (forward_map, reverse_map).
        """
    def __len__(self) -> int:
        """
        :returns: The number of unique values seen so far.
        """
