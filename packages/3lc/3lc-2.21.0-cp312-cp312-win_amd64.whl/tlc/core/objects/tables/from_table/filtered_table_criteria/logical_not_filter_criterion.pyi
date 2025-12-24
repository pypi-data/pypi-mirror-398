from collections.abc import Mapping
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.schema import DictValue as DictValue, Schema as Schema
from typing import Any

class LogicalNotFilterCriterion(FilterCriterion):
    filter_criterion: FilterCriterion
    def __init__(self, filter_criterion: FilterCriterion | None = None, init_parameters: Any = None) -> None:
        """A predicate that is the logical not of a filter criteria.

        :param filter_criterion: The input filter criterion.
        """
    @staticmethod
    def from_any(any_value: FilterCriterion | Mapping) -> FilterCriterion: ...
