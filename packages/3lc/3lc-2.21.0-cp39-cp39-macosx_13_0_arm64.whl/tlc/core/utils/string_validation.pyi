from _typeshed import Incomplete

logger: Incomplete

def validate_project_name(name: str) -> None:
    """Validate a project name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def validate_dataset_name(name: str) -> None:
    """Validate a dataset name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def validate_table_name(name: str) -> None:
    """Validate a table name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def validate_run_name(name: str) -> None:
    """Validate a run name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def validate_column_name(name: str) -> None:
    """Validate a column name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def validate_map_element_name(name: str) -> None:
    """Validate a map element name.

    Raises a ValueError if the name contains any illegal characters.
    :param name: The name to validate.
    :raises ValueError: If the name contains any illegal characters.
    """
def warn_if_invalid_column_name(name: str) -> None:
    """Warn if a column name is invalid.

    This function exists for backwards compatibility with tables created before the introduction of the column name
    validation. It will log a warning if the column name is invalid, but will not raise an error.

    :param name: The name to validate.
    """
def warn_if_invalid_map_element_name(name: str) -> None:
    """Warn if a map element name is invalid.

    This function exists for backwards compatibility with tables created before the introduction of the map element name
    validation. It will log a warning if the map element name is invalid, but will not raise an error.

    :param name: The name to validate.
    """
