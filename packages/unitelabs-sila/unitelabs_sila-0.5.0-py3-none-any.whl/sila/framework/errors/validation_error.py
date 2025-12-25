import typing_extensions as typing

from ..protobuf import Reader, WireType, Writer
from .sila_error import SiLAError


class ValidationError(SiLAError):
    """
    Error that occurs when command parameters are missing or invalid.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
      parameter: The command parameter for which the validation error
        occurred.
    """

    def __init__(self, message: str, parameter: str) -> None:
        super().__init__(message, parameter)

    @property
    def parameter(self) -> str:
        """The parameter for which the validation error occurred."""

        return self.args[1]

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = ""
        parameter = ""
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                parameter = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message = reader.read_string()
            else:
                reader.skip_type(tag & 7)

        return cls(message, parameter)

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        writer.write_uint32(10).fork()

        if self.parameter:
            writer.write_uint32(10).write_string(self.parameter)
        if self.message:
            writer.write_uint32(18).write_string(self.message)

        writer.ldelim()

        if number:
            writer.ldelim()

        return writer.finish()
