import typing_extensions as typing

from ..protobuf import Reader, WireType, Writer
from .sila_error import SiLAError


class UndefinedExecutionError(SiLAError):
    """
    Unexpected error that occurs during command execution.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str = "", *args: object) -> None:
        super().__init__(message, *args)

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = ""
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                message = reader.read_string()
            else:
                reader.skip_type(tag & 7)

        return cls(message)

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        writer.write_uint32(26).fork()

        if self.message:
            writer.write_uint32(10).write_string(self.message)

        writer.ldelim()

        if number:
            writer.ldelim()

        return writer.finish()
