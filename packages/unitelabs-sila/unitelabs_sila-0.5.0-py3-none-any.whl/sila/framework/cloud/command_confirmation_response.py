import dataclasses

import typing_extensions as typing

from ..command import CommandConfirmation
from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class CommandConfirmationResponse(Message):
    """
    Message that confirms the execution of a SiLA command.

    Attributes:
      command_confirmation: The confirmation of the executed command.
    """

    command_confirmation: CommandConfirmation = dataclasses.field(default_factory=CommandConfirmation)

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                message.command_confirmation = CommandConfirmation.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        self.command_confirmation.encode(writer, 1)

        if number:
            writer.ldelim()

        return writer.finish()
