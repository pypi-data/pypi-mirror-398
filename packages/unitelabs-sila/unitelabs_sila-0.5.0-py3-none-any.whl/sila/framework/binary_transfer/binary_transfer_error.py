import enum

import typing_extensions as typing

from ..errors import SiLAError
from ..protobuf import Reader, WireType, Writer


class BinaryTransferErrorType(enum.IntEnum):
    """Type of errors that occur during binary transfer operations."""

    INVALID_BINARY_TRANSFER_UUID = 0
    """
    Is issued if the provided binary transfer UUID is invalid or not
    recognized.
    """

    BINARY_UPLOAD_FAILED = 1
    """Is issued when the upload of binary data has failed."""

    BINARY_DOWNLOAD_FAILED = 2
    """Is issued when the download of binary data has failed."""


class BinaryTransferError(SiLAError):
    """
    Error that occurs during binary transfer operations.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
      error_type: The type of error that occurred.
    """

    Type: typing.ClassVar[type[BinaryTransferErrorType]] = BinaryTransferErrorType

    def __init__(self, message: str, error_type: BinaryTransferErrorType) -> None:
        super().__init__(message, error_type)

    @property
    def error_type(self) -> BinaryTransferErrorType:
        """The type of error that occurred."""

        return self.args[1]

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = ""
        error_type = BinaryTransferErrorType.INVALID_BINARY_TRANSFER_UUID
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.VARINT)
                error_type = BinaryTransferErrorType(reader.read_int32())
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

        if self.error_type:
            writer.write_uint32(8).write_int32(self.error_type)
        if self.message:
            writer.write_uint32(18).write_string(self.message)

        if number:
            writer.ldelim()

        return writer.finish()


class InvalidBinaryTransferUUID(BinaryTransferError):
    """
    Raised when the provided identifier is invalid or not recognized.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str, *args) -> None:
        super().__init__(message, BinaryTransferErrorType.INVALID_BINARY_TRANSFER_UUID)


class BinaryUploadFailed(BinaryTransferError):
    """
    Raised when the upload of binary data has failed.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str, *args) -> None:
        super().__init__(message, BinaryTransferErrorType.BINARY_UPLOAD_FAILED)


class BinaryDownloadFailed(BinaryTransferError):
    """
    Raised when the download of binary data has failed.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str, *args) -> None:
        super().__init__(message, BinaryTransferErrorType.BINARY_DOWNLOAD_FAILED)
