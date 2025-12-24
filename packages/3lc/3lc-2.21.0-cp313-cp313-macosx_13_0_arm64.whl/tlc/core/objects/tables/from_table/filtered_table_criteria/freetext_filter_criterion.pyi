from collections.abc import Mapping
from tlc.core.builtins.constants.string_roles import STRING_ROLE_SEARCH as STRING_ROLE_SEARCH
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.schema import BoolValue as BoolValue, MapElement as MapElement, NumericValue as NumericValue, Schema as Schema, StringValue as StringValue
from typing import Any

class FreeTextFilterCriterion(FilterCriterion):
    '''FreeTextFilterCriterion is a criterion that matches across the whole row

    It splits the the search string into parts and matches each part against all columns of the row. A match is found if
    all parts are found at least once in any column of the row.

    Examples:
      search, row, match, comment
      "A", {"col_1": "A", "col_2": "B"} => True, only part found in col 1
      "A B", {"col_1": "ABC", "col_2": "DEF"} => True, all parts are found in col_1
      "A B", {"col_1": "ACE", "col_2": "BDF"} => True, part 1 in col_1, part 2 in col_2
      "cat", {"label": 1} => True, given a ValueMap with {1:"cat"}
    '''
    freetext_search_string: str
    use_case_insensitive_search: bool
    def __init__(self, negate: bool | None = None, freetext_search_string: str | None = None, use_case_insensitive_search: bool | None = None, init_parameters: Any = None) -> None: ...
    @staticmethod
    def from_any(any_filter_criterion: FilterCriterion | Mapping) -> FreeTextFilterCriterion: ...
