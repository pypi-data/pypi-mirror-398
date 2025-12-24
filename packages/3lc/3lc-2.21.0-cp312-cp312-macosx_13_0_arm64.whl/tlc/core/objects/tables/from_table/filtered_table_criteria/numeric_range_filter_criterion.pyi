from collections.abc import Mapping
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import ColumnFilterCriterion as ColumnFilterCriterion, FilterCriterion as FilterCriterion
from tlc.core.schema import Float32Value as Float32Value, Schema as Schema
from typing import Any

class NumericRangeFilterCriterion(ColumnFilterCriterion):
    value_range_min: int | float
    value_range_max: int | float
    def __init__(self, attribute: str | None = None, min_value: int | float | None = None, max_value: int | float | None = None, init_parameters: Any = None) -> None: ...
    @staticmethod
    def from_any(any_filter_criterion: FilterCriterion | Mapping) -> NumericRangeFilterCriterion: ...
