import enum

import typing_extensions as typing

from ..protobuf import Reader, WireType, Writer
from .sila_error import SiLAError


class FrameworkErrorType(enum.IntEnum):
    """Type of errors that occur when SiLA 2 is used incorrectly."""

    COMMAND_EXECUTION_NOT_ACCEPTED = 0
    """
    Is issued if the SiLA server does not allow the command execution
    because it is occupied handling other command executions.
    """

    INVALID_COMMAND_EXECUTION_UUID = 1
    """
    Is issued if the provided command execution UUID is invalid or
    not recognized.
    """

    COMMAND_EXECUTION_NOT_FINISHED = 2
    """Is issued if the response to an unfinished command is requested."""

    INVALID_METADATA = 3
    """Is issued if metadata is missing or invalid."""

    NO_METADATA_ALLOWED = 4
    """Is issued if providing metadata is not allowed."""


class FrameworkError(SiLAError):
    """
    Error that occurs when SiLA 2 is used incorrectly.

    Args:
      error_type: The type of error that occurred.
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    Type: typing.ClassVar[type[FrameworkErrorType]] = FrameworkErrorType

    def __init__(self, message: str, error_type: FrameworkErrorType) -> None:
        super().__init__(message, error_type)

    @property
    def error_type(self) -> FrameworkErrorType:
        """The type of error that occurred."""

        return self.args[1]

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = ""
        error_type = FrameworkErrorType.COMMAND_EXECUTION_NOT_ACCEPTED
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.VARINT)
                error_type = FrameworkErrorType(reader.read_int32())
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message = reader.read_string()
            else:
                reader.skip_type(tag & 7)

        return cls(message, error_type)

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        writer.write_uint32(34).fork()

        if self.error_type:
            writer.write_uint32(8).write_int32(self.error_type)
        if self.message:
            writer.write_uint32(18).write_string(self.message)

        writer.ldelim()

        if number:
            writer.ldelim()

        return writer.finish()


class CommandExecutionNotAccepted(FrameworkError):
    """
    Raised when the server does not allow further command executions.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message, FrameworkErrorType.COMMAND_EXECUTION_NOT_ACCEPTED)


class InvalidCommandExecutionUUID(FrameworkError):
    """
    Raised when the provided identifier is invalid or not recognized.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message, FrameworkErrorType.INVALID_COMMAND_EXECUTION_UUID)


class CommandExecutionNotFinished(FrameworkError):
    """
    Raised when the response to an unfinished command is requested.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message, FrameworkErrorType.COMMAND_EXECUTION_NOT_FINISHED)


class InvalidMetadata(FrameworkError):
    """
    Raised when metadata is missing or invalid.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message, FrameworkErrorType.INVALID_METADATA)


class NoMetadataAllowed(FrameworkError):
    """
    Raised when providing metadata is not allowed.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "") -> None:
        super().__init__(message, FrameworkErrorType.NO_METADATA_ALLOWED)
