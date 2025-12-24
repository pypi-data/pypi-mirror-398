from collections.abc import Iterable, Sequence
from rich.progress import ProgressColumn as ProgressColumn, ProgressType as ProgressType

rich_track_in_progress: bool

def track(sequence: Sequence[ProgressType] | Iterable[ProgressType], description: str = '', show_speed: bool = True, total: float | None = None, refresh_per_second: float | None = None, update_period: float = 0.2) -> Iterable[ProgressType]:
    """Create a progress bar for a sequence of items.

    :param sequence: The sequence of items to iterate over.
    :param description: The description to display.
    :param show_speed: Show the speed of the progress bar.
    :param total: The total number of items in the sequence.
    :param refresh_per_second: The number of times per second to refresh the progress bar.
    :param update_period: The minimum time between updates.
    :return: An iterable that yields the items in the sequence whilst displaying a progress bar.
    """
