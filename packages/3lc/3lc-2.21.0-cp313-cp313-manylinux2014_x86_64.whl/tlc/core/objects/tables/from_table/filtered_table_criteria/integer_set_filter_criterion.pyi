from collections.abc import Mapping
from tlc.core.builtins.constants.number_roles import NUMBER_ROLE_INDEX as NUMBER_ROLE_INDEX
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import ColumnFilterCriterion as ColumnFilterCriterion, FilterCriterion as FilterCriterion
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Schema as Schema, Uint64Value as Uint64Value
from typing import Any

class IntegerSetFilterCriterion(ColumnFilterCriterion):
    integer_set: list[int]
    def __init__(self, negate: bool | None = None, attribute: str | None = None, integer_set: list[int] | None = None, init_parameters: Any = None) -> None: ...
    @staticmethod
    def from_any(any_filter_criterion: FilterCriterion | Mapping) -> IntegerSetFilterCriterion: ...
