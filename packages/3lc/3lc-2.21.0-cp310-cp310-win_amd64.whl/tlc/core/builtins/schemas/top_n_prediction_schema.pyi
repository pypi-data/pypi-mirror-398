from tlc.core.builtins.constants.column_names import CONFIDENCE as CONFIDENCE, LABEL as LABEL
from tlc.core.schema import DimensionNumericValue as DimensionNumericValue, Float32Value as Float32Value, Int32Value as Int32Value, MapElement as MapElement, Schema as Schema

def top_n_prediction_schema() -> Schema:
    """
    Returns a standard top-N schema where predictions and confidences are interleaved in a single fixed-size list
    """
