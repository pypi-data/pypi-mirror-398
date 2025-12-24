import abc
from _typeshed import Incomplete
from abc import abstractmethod
from collections.abc import Mapping
from tlc.core.json_helper import JsonHelper as JsonHelper
from tlc.core.object import Object as Object
from tlc.core.schema import ObjectTypeStringValue as ObjectTypeStringValue, Schema as Schema, StringValue as StringValue
from typing import Any

logger: Incomplete

class FilterCriterion(Object, metaclass=abc.ABCMeta):
    """The base class for all filter criteria.

    A filter criterion is a predicate that can be applied to a row's attributes to determine whether the
    row matches the criterion.
    """
    def __init__(self, init_parameters: Any = None) -> None: ...
    def filter_matches(self, row: Any, schema: Schema | None) -> bool:
        """Determines whether the filter criterion matches the given row.

        :param row: The row to test.
        :param schema: The schema of the row.

        :Returns: True if the row matches the filter criterion, False otherwise.
        """
    @staticmethod
    @abstractmethod
    def from_any(any_value: Mapping | FilterCriterion) -> FilterCriterion: ...
    def to_minimal_dict(self, include_all: bool) -> dict[str, Any]:
        """Provide an alternative way of serialization for FilterCriterion.

        We don't have polymorphic schemas on the Table-level so we need a way of making FilterCriteria into a dict, Ref
        json_helpers.py
        """

class ColumnFilterCriterion(FilterCriterion, metaclass=abc.ABCMeta):
    attribute: str
    def __init__(self, attribute: str | None = None, init_parameters: Any = None) -> None:
        """A filter criterion who's predicate is only applied to a single column or attribute of the row.

        :param attribute: The name of the attribute to which the criterion applies.
        """
