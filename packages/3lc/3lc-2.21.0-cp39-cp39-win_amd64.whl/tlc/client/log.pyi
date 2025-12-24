from tlc.client.session import Session as Session
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.url import Url as Url
from typing import Any

def log(data: dict[str, Any], run: Run | Url | None = None) -> None:
    """Log output data to the active Run or a specified Run.

    If keys 'epoch' or 'iteration' are present in the data, charts for the logged data will be created against those
    values in the Runs overview in the Dashboard.

    :::{note}
    This function is intended for logging output data for a Run as a whole, or aggregated over an epoch or iteration.
    For logging data for individual samples, refer to the {ref}`Collect Metrics <collect-metrics>` section in the User
    Guide.
    :::

    :param data: The data to log.
    :param run: The Run to log the data to. If not provided, the active Run will be used.
    :raises ValueError: If no Run is provided and there is no active Run.
    """
