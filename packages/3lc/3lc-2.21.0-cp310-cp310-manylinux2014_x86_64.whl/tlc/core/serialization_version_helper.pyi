from _typeshed import Incomplete

logger: Incomplete

class SerializationVersionHelper:
    """A class with helper methods for working with Object/Schema versions"""
    @staticmethod
    def compare_versions(input_version: str, current_version: str) -> None:
        """Compare the input version to the current version of the."""
