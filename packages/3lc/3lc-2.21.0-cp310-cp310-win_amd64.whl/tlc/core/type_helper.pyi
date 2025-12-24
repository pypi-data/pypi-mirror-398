from typing import Any

class TypeHelper:
    """
    A class with helper methods for working with atomic values described using type strings (int32, float64, bool, etc.)
    """
    @staticmethod
    def from_any(value: Any, atomic_type: str) -> Any:
        """
        Casts a value according to a type string
        """
    @staticmethod
    def is_list_of_dicts(value: Any) -> bool:
        """
        Checks if a value is a list of dictionaries
        """
    @staticmethod
    def is_iterable(value: Any) -> bool:
        """
        Checks if a value is iterable
        """
