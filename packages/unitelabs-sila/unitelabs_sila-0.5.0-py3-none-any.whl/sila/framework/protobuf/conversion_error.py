import collections.abc

import typing_extensions as typing


class ConversionError(Exception):
    """
    Raised when converting operations encounter invalid data.

    Args:
      message: An explanation of why the conversion error occurred.
      path: The path to the element where the error occurred.
    """

    def __init__(self, message: str, path: typing.Optional[collections.abc.Sequence[typing.Union[int, str]]] = None):
        super().__init__(message, list(path) if path is not None else [])

    @property
    def message(self) -> str:
        """An explanation of why the conversion error occurred."""

        return self.args[0]

    @property
    def path(self) -> collections.abc.Sequence[str]:
        """The path to the element where the error occurred."""

        return self.args[1]

    @typing.override
    def __str__(self) -> str:
        return self.message
