import subprocess
from _typeshed import Incomplete
from types import TracebackType
from typing import Any

class SubprocessWithParentTerminationBase:
    '''Create a subprocess that will terminate when the parent process dies.

    This is useful for creating subprocesses that should be terminated when the parent process dies even if the parent
    dies unexpectedly or forcefully.

    As a convenience the class also provides a context manager interface that will terminate the subprocess when the
    context is exited:

        ```python
        with SubprocessWithParentTermination(["ls", "-l"]) as process:
            process.wait()
        ```

    '''
    process: Incomplete
    timeout: Incomplete
    def __init__(self, process: subprocess.Popen, timeout: float | None) -> None: ...
    def terminate(self) -> None:
        """Terminate the subprocess gracefully."""
    def kill(self) -> None:
        """Kill the subprocess forcefully."""
    def wait(self, timeout: float | None = None) -> int:
        """Wait for the subprocess to complete.

        :param timeout: Timeout in seconds, or None for no timeout.
        :returns: Return code of the subprocess.
        """
    def poll(self) -> int | None:
        """Check if the subprocess is still running.

        :returns: Return code if finished, None if still running.
        """
    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the underlying process."""
    def __enter__(self) -> SubprocessWithParentTerminationBase:
        """Context manager entry."""
    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, traceback: TracebackType) -> None:
        """Context manager exit with cleanup."""

class SubprocessWithParentTermination(SubprocessWithParentTerminationBase):
    """Linux implementation using prctl with PDEATHSIG."""
    def __init__(self, *args: Any, timeout: float | None = None, **kwargs: Any) -> None: ...
