from tlc.core.schema import Int32Value as Int32Value, MapElement as MapElement, Schema as Schema

def row_count_schema() -> Schema:
    """
    Returns a standard row count schema describing the number of rows in a table
    """
