from _typeshed import Incomplete
from tlc.core.builtins.constants.column_names import RUN_STATUS as RUN_STATUS, RUN_STATUS_COMPLETED as RUN_STATUS_COMPLETED, RUN_STATUS_RUNNING as RUN_STATUS_RUNNING
from tlc.core.objects.mutable_objects.run import Run as Run
from tlc.core.objects.tables.system_tables.indexing_tables.config_indexing_table import ConfigIndexingTable as ConfigIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.run_indexing_table import RunIndexingTable as RunIndexingTable
from tlc.core.objects.tables.system_tables.indexing_tables.table_indexing_table import TableIndexingTable as TableIndexingTable
from tlc.core.objects.tables.system_tables.timestamp_helper import TimestampHelper as TimestampHelper
from tlc.core.url import Url as Url
from tlc.core.url_adapter import IfExistsOption as IfExistsOption
from typing import Any, Literal

logger: Incomplete

class Session:
    """Session singleton for interacting with 3LC objects.

    The session object is used to create and manage 3LC objects, such as Runs.
    The session holds the current active Run object and is managed by calls to `tlc.init()` and `tlc.close()`.
    """
    def __new__(cls) -> Session: ...
    def __init__(self) -> None: ...
    @staticmethod
    def initialize_run(project_name: str, run_name: str, run_url: Url | None = None, description: str | None = None, parameters: dict[str, Any] | None = None, if_exists_option: IfExistsOption = ..., root_url: Url | str | None = None) -> str:
        '''Creates a new active Run object.

        :param project_name: Name of the project.
        :param run_name: Name of the Run.
        :param run_url: Url to the run. If provided, project_name and run_name are ignored and the run will be created
            at the provided url. If the url already exists, the if_exists argument is used to determine how to proceed.
        :param description: Description of the run.
        :param parameters: Parameters of the run.
        :param if_exists_option: How to deal with existing runs. Options are "reuse", "overwrite", "rename", "raise".

        :returns: Absolute URL to where the created Run object can be accessed.
        '''
    def close(self) -> None:
        """Closes the current session.

        This method stops all background indexers and deletes the current session instance.
        """
    @property
    def run(self) -> Run | None:
        """
        Returns the active run object, if a run is initialized.
        """
    run_url: Incomplete
    def set_active_run(self, run: Run | Url | str) -> None:
        """Set the active Run.

        :param run: The Run object or URL to set as the active run.
        """

def init(project_name: str | None = None, run_name: str | None = None, description: str | None = None, parameters: dict[str, Any] | None = None, if_exists: Literal['reuse', 'overwrite', 'rename', 'raise'] = 'rename', *, root_url: Url | str | None = None, run_url: Url | str | None = None) -> Run:
    '''Initialize a 3LC Run.

    Initializes a 3LC Run object and sets it as the active run for the current session.
    Starts the 3LC indexing threads.

    :param project_name: Name of the project. If empty, the run will be stored under a default project.
    :param run_name: Name of the Run. If empty, a random name will be generated.
    :param description: Description of the run.
    :param parameters: Parameters of the run.
    :param if_exists: How to deal with existing runs. Options are "reuse", "overwrite", "rename", "raise".
    :param root_url: The root url to use. If not provided, the project root url will be used.
    :param run_url: Url to the run. If provided, root_url, project_name and run_name are ignored and the run will be
        created at the provided url. If the url already exists, the if_exists argument is used to determine how to
        proceed.
    :returns: A Run object.
    '''
def close() -> None:
    """Close a run session

    Recommended to call at the end of training to make sure, all training data hook is saved.
    It blocks the running until all data hooks are saved.
    """
