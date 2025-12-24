class TLCException(Exception):
    """Base class for all TLC exceptions."""
class ConfigNotFound(TLCException):
    """Raised when a config file is not found."""
