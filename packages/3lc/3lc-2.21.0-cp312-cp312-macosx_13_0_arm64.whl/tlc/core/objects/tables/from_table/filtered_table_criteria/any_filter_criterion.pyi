from collections.abc import Mapping
from tlc.core.objects.tables.from_table.filtered_table_criteria.all_filter_criterion import CriteriaListFilterCriterion as CriteriaListFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.schema import Schema as Schema
from typing import Any

class AnyFilterCriterion(CriteriaListFilterCriterion):
    def __init__(self, filter_criteria: list[FilterCriterion] | None = None, init_parameters: Any = None) -> None:
        """A predicate that is the logical or-combination of a list of filter criteria.

        Equivalent to the python any() function.

        :param filter_criteria: The list of input filter criteria.
        """
    @staticmethod
    def from_any(any_value: FilterCriterion | Mapping) -> FilterCriterion: ...
