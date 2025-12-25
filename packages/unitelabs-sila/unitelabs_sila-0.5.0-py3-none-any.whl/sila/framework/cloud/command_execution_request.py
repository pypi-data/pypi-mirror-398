import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer
from .command_parameter import CommandParameter


@dataclasses.dataclass
class CommandExecutionRequest(Message):
    """
    Message to execute a SiLA command.

    Attributes:
      fully_qualified_command_id: The fully qualified identifier of
        the command to be executed.
      command_parameter: The command parameters.
    """

    fully_qualified_command_id: str = ""
    command_parameter: CommandParameter = dataclasses.field(default_factory=CommandParameter)

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
                message.fully_qualified_command_id = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.command_parameter = CommandParameter.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.fully_qualified_command_id:
            writer.write_uint32(10).write_string(self.fully_qualified_command_id)
        self.command_parameter.encode(writer, 2)

        if number:
            writer.ldelim()

        return writer.finish()
