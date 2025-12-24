from _typeshed import Incomplete
from collections.abc import Generator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from tlc.core.url import Url as Url
from typing import Any

logger: Incomplete

class _DisabledContextType:
    """Sentinel for disabled project context."""

@contextmanager
def disabled_project_context() -> Generator[_DisabledContextType, None, None]:
    """
    Context manager that sets the project context to a disabled sentinel value.

    Restores the previous context on exit.
    """

@dataclass
class ProjectContext:
    """Project context objects that provide project-related information.

    This class provides context about a project, including its root directory and name.
    This is used to determine where to store project-specific information like timestamps and indexes.
    """
    project_root: Url
    project_name: str
    def __enter__(self) -> ProjectContext | None | _DisabledContextType:
        """
        Enter the context manager, setting this instance as the current project context.

        :return: The current ProjectContext instance.
        """
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit the context manager, restoring the previous project context.
        """
    @staticmethod
    def get_context() -> ProjectContext | None | _DisabledContextType:
        """
        Get the project context for the current thread.

        :return: The project context, None if not set.
        """
    @staticmethod
    def get_project_context_from_url(url: Url) -> ProjectContext | None:
        """
        Get the project context from a URL.

        :param url: The URL to analyze.
        :return: The deduced ProjectContext or None if not applicable.
        """
    @staticmethod
    def get_project_context_from_default_alias_url(default_alias_url: Url) -> ProjectContext | None:
        """
        Get the project context from a default aliases URL.

        Default aliases (SECONDARY) can be placed:
           1. In the root of the 3LC directory structure. This is alongside PRIMARY config files
           2. In a projects directory (root/project_a), which makes the config file associated with a project.

        :param default_alias_url: The URL of the default alias config.
        :return: The deduced ProjectContext or None if not applicable.
        """
    @staticmethod
    def get_project_context_from_config_url(config_url: Url) -> ProjectContext | None:
        """
        Get the project context from a config file URL.

        Config files (PRIMARY) are placed in the root of the 3LC directory structure. Therefore the timestamp URL is a
        sibling of the config URL. These files do not have a project name.

        :param config_url: The URL of the config file.
        :return: The deduced ProjectContext or None if not applicable.
        """
    @staticmethod
    def get_project_context_from_object_url(object_url: Url) -> ProjectContext | None:
        """
        Get the project context from an object URL.

        :param object_url: The URL of the object.
        :return: The deduced ProjectContext or None if not applicable.
        """
    @staticmethod
    def push_scope(ctx: ProjectContext | None | _DisabledContextType) -> AbstractContextManager[ProjectContext | None | _DisabledContextType]:
        """
        Push a context onto the stack and return a context manager that will restore the previous context.

        :param ctx: The context to push.
        :return: A context manager that will restore the previous context when exited.
        """
