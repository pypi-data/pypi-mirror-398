import collections.abc

import typing_extensions as typing


class DecodeError(Exception):
    """
    Raised when decoding operations encounter invalid or insufficient data.

    Args:
      message: An explanation of why the decoding error occurred.
      offset: The position in the data where the error occurred.
      path: The path to the element where the error occurred.
    """

    def __init__(
        self, message: str, offset: int, path: typing.Optional[collections.abc.Sequence[typing.Union[int, str]]] = None
    ):
        super().__init__(message, offset, list(path) if path is not None else [])

    @property
    def message(self) -> str:
        """An explanation of why the decoding error occurred."""

        return self.args[0]

    @property
    def offset(self) -> int:
        """The position in the data where the error occurred."""

        return self.args[1]

    @property
    def path(self) -> collections.abc.Sequence[typing.Union[int, str]]:
        """The path to the element where the error occurred."""

        return self.args[2]

    @typing.override
    def __str__(self) -> str:
        return self.message
