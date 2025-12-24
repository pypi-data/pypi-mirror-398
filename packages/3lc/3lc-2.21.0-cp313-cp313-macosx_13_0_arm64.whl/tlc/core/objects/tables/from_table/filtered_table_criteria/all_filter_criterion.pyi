import abc
from collections.abc import Mapping, Sequence
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_INDEX as NUMBER_ROLE_INDEX
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.schema import DictValue as DictValue, DimensionNumericValue as DimensionNumericValue, Schema as Schema
from typing import Any

class CriteriaListFilterCriterion(FilterCriterion, metaclass=abc.ABCMeta):
    filter_criteria: list[FilterCriterion]
    def __init__(self, filter_criteria: Sequence[FilterCriterion] | None = None, init_parameters: Any = None) -> None:
        """A predicate that is the logical and-combination of a list of filter criteria.

        :param filter_criteria: The input filter criteria.
        """
    def to_minimal_dict(self, include_all: bool) -> dict[str, Any]:
        """Returns a minimal dictionary representation of the object.

        :param include_all: Whether to include all properties, or only those that are required to reconstruct the
            object.
        """

class AllFilterCriterion(CriteriaListFilterCriterion):
    def __init__(self, filter_criteria: Sequence[FilterCriterion] | None = None, init_parameters: Any = None) -> None:
        """A predicate that is the logical and-combination of a list of filter criteria.

        This is equivalent to the python all(f1, f2, ...) function.

        :param filter_criteria: A list of filter criteria.
        """
    @staticmethod
    def from_any(any_value: FilterCriterion | Mapping) -> FilterCriterion: ...
