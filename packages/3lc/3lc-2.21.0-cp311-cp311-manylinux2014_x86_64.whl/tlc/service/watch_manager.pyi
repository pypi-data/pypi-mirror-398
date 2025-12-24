from _typeshed import Incomplete
from tlc.core.objects.mutable_objects.configuration import Configuration as Configuration
from tlc.core.url import Url as Url
from tlc.utils.subprocess_with_parent_termination import SubprocessWithParentTermination as SubprocessWithParentTermination

logger: Incomplete

def start_watch_subprocess() -> SubprocessWithParentTermination | None:
    """Start the watch service in a subprocess with automatic parent termination.

    :returns: The subprocess wrapper object if started successfully, None otherwise.
    """
def stop_watch_subprocess(process_wrapper: SubprocessWithParentTermination) -> None:
    """Stop the watch subprocess gracefully.

    :param process_wrapper: The subprocess wrapper to stop.
    """
def is_watch_enabled() -> bool:
    """Check if the watch service is enabled in configuration.

    :returns: True if watch service is enabled, False otherwise.
    """
