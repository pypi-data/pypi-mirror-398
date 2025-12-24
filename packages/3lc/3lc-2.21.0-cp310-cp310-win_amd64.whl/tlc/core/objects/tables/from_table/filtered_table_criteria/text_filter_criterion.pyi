from collections.abc import Mapping
from tlc.core.builtins.constants.string_roles import STRING_ROLE_SEARCH as STRING_ROLE_SEARCH
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import ColumnFilterCriterion as ColumnFilterCriterion, FilterCriterion as FilterCriterion
from tlc.core.schema import BoolValue as BoolValue, Schema as Schema, StringValue as StringValue
from typing import Any

class TextFilterCriterion(ColumnFilterCriterion):
    text_search_string: str
    use_case_insensitive_search: bool
    def __init__(self, attribute: str | None = None, text_search_string: str | None = None, use_case_insensitive_search: bool | None = None, init_parameters: Any = None) -> None: ...
    @staticmethod
    def from_any(any_filter_criterion: FilterCriterion | Mapping) -> TextFilterCriterion: ...
