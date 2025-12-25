import collections.abc

import typing_extensions as typing


class ParseError(Exception):
    """
    Raised when XML parsing operations encounter unexpected or invalid data.

    Args:
      message: An explanation of why the parsing error occurred.
      path: The path to the element where the error occurred.
      line: The line number in which the current error occurred.
      column: The column number in which the current error occurred.
    """

    def __init__(
        self,
        message: str,
        /,
        *,
        path: typing.Optional[collections.abc.Sequence[str]] = None,
        line: int = -1,
        column: int = -1,
    ):
        super().__init__(message, list(path) if path is not None else [], line, column)

    @property
    def message(self) -> str:
        """An explanation of why the conversion error occurred."""

        return self.args[0]

    @property
    def path(self) -> collections.abc.Sequence[str]:
        """The path to the element where the error occurred."""

        return self.args[1]

    @property
    def line(self) -> int:
        """The line number in which the current error occurred."""

        return self.args[2]

    @property
    def column(self) -> int:
        """The column number in which the current error occurred."""

        return self.args[3]

    @typing.override
    def __str__(self) -> str:
        return self.args[0]
