from .sila_error import SiLAError


class SiLAConnectionError(SiLAError):
    """
    Error that occurs in the underlying communication infrastructure.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """
