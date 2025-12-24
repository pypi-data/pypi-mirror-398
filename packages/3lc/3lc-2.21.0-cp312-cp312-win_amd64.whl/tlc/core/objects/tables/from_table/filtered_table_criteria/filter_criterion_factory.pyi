from collections.abc import Mapping
from tlc.core.objects.tables.from_table.filtered_table_criteria.all_filter_criterion import AllFilterCriterion as AllFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.any_filter_criterion import AnyFilterCriterion as AnyFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.bool_filter_criterion import BoolFilterCriterion as BoolFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.filter_criterion import FilterCriterion as FilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.freetext_filter_criterion import FreeTextFilterCriterion as FreeTextFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.integer_set_filter_criterion import IntegerSetFilterCriterion as IntegerSetFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.logical_not_filter_criterion import LogicalNotFilterCriterion as LogicalNotFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.numeric_range_filter_criterion import NumericRangeFilterCriterion as NumericRangeFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.region_filter_criterion import Region2DFilterCriterion as Region2DFilterCriterion, Region3DFilterCriterion as Region3DFilterCriterion
from tlc.core.objects.tables.from_table.filtered_table_criteria.text_filter_criterion import TextFilterCriterion as TextFilterCriterion

def create_optional_filter(any_value: FilterCriterion | Mapping | None) -> FilterCriterion | None: ...
def create_filter(any_value: FilterCriterion | Mapping) -> FilterCriterion: ...
