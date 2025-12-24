from tlc.core.json_helper import JsonHelper as JsonHelper
from tlc.core.objects.mutable_objects.run import Run as Run
from typing import Any, TypedDict

class ProjectInfo(TypedDict):
    num_runs: int
    num_tables: int
    num_datasets: int
    run_statuses: dict[str, int]
    table_row_count: int
    num_metrics_tables: int
    metric_table_row_count: int
    metric_table_byte_count: int

def get_project_usage_metadata() -> dict[str, Any]: ...
def compute_project_usage_metadata(wait_for_complete_index: bool = False) -> None:
    """Get project usage metadata from the table and run indexers"""
