import typing_extensions as typing


class EncodeError(Exception):
    """
    Raised when encoding operations encounter invalid or insufficient data.

    Args:
      message: An explanation of why the encoding error occurred.
    """

    def __init__(self, message: str):
        super().__init__(message)

    @property
    def message(self) -> str:
        """An explanation of why the encoding error occurred."""

        return self.args[0]

    @typing.override
    def __str__(self) -> str:
        return self.message
