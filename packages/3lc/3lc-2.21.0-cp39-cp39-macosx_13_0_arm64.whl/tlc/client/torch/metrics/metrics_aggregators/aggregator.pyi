import abc
from abc import abstractmethod
from tlc.core.schema import Schema as Schema
from typing import Any, final

class Aggregator(metaclass=abc.ABCMeta):
    """Base class for aggregating metrics across multiple batches of data.

    This class is designed to be extended by specific types of aggregators that implement their own logic for computing
    aggregate metrics from a batch of data and across multiple batches.

    A single input metric can result in 0 or more output metrics, depending on the data type and schema of the input
    metric.
    """
    def __init__(self) -> None: ...
    def reset(self) -> None:
        """Resets the internal state of the aggregator."""
    @final
    def column_schemas_finalized(self) -> bool:
        """Checks if column schemas have been finalized.

        :returns: True if the column schemas are set, otherwise False.
        """
    @final
    def set_column_schemas(self, column_schemas: dict[str, Schema]) -> None:
        """Sets the column schemas used for aggregation.

        The column schemas are used to determine which columns are computable and how to compute aggregate values from
        them. If columns are missing a schema, a inferred schema will be used.

        :param column_schemas: A dictionary mapping column names to their respective schemas.
        """
    @final
    def aggregate_batch(self, computed_metrics: dict[str, list[Any]]) -> None:
        """Aggregate metrics for a single batch.

        This method computes the aggregate metrics for a single batch and updates the internal state
        accordingly.

        :param computed_metrics: A dictionary containing the computed metrics for each column in the batch.
        """
    @final
    def finalize_aggregates(self) -> dict[str, Any]:
        """Finalizes the aggregation process and returns the aggregate metrics.

        :returns: A dictionary containing the final aggregate metrics across all batches.
        """
    @abstractmethod
    def compute_batch_aggregate(self, computed_metrics: dict[str, list[Any]]) -> dict[str, Any]:
        """Computes the aggregate metrics for a single batch.

        This is an abstract method that must be implemented in subclasses.

        :param computed_metrics: A dictionary containing the computed metrics for each column in the batch.
        :returns: A dictionary containing the aggregate metrics for this batch.
        """
    @abstractmethod
    def aggregate_across_batches(self) -> dict[str, Any]:
        """Computes the final aggregate metrics across all batches.

        This is an abstract method that must be implemented in subclasses.

        :returns: A dictionary containing the final aggregate metrics.
        """
