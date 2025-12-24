from collections.abc import Mapping
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import ColumnFilterCriterion as ColumnFilterCriterion, FilterCriterion as FilterCriterion
from tlc.core.schema import BoolValue as BoolValue, Schema as Schema
from typing import Any

class BoolFilterCriterion(ColumnFilterCriterion):
    """A BoolFilterCriterion is a predicate that can be applied to an object's attribute to determine whether the
    object matches the criterion.
    """
    bool_value: bool
    def __init__(self, attribute: str | None = None, bool_value: bool | None = None, init_parameters: Any = None) -> None:
        """Initialize a new BoolFilterCriterion.

        :param attribute: The name of the attribute to which the criterion applies.
        :param bool_value: The boolean value to match.
        :param init_parameters: The initial parameters for the creating the criterion.
        """
    @staticmethod
    def from_any(any_filter_criterion: Mapping | FilterCriterion) -> BoolFilterCriterion: ...
