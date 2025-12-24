from tlc.core.schema import DictValue as DictValue, Schema as Schema, StringValue as StringValue
from tlc.core.url import Url as Url
from typing import Any

class JsonHelper:
    """A class with helper methods for working with JSON strings"""
    @staticmethod
    def sort_by_rank(data: dict[str, Any], rankings: list[tuple[str, int]], default_rank: int = 0) -> dict[str, Any]:
        """Helper to (stable) sort a dictionary based on input ranks.

        Given a list of tuples with keys and their rank, sort the dictionary such that the items with lowest rank
        appear first.
         - Lower rank items are sorted before higher rank items.
         - If a key is not found in the rank list, it is assigned the default_rank.
         - Add a key with a negative rank to sort it before the default_rank.
         - All keys with the same rank are sorted based on order in the input dictionary.
         - Only top-level keys are sorted. Nested keys are not sorted.
        """
    @staticmethod
    def to_minimal_dict(this_object: Any, schema: Schema, include_all: bool, include_transient: bool = False) -> dict[str, Any]:
        """
        Returns a dict where only non-default values are included.
        """
