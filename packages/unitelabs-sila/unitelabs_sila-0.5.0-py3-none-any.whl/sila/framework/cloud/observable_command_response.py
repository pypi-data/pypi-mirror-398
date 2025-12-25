import dataclasses

import typing_extensions as typing

from ..command import CommandExecutionUUID
from ..protobuf import DecodeError, Message, Reader, WireType, Writer


@dataclasses.dataclass
class ObservableCommandResponse(Message):
    """
    The response of the executed SiLA command.

    Attributes:
      command_execution_uuid: The command execution identifier of the
        command the response was created by.
      value: The response of the command.
    """

    command_execution_uuid: CommandExecutionUUID = dataclasses.field(default_factory=CommandExecutionUUID)
    response: bytes = b""

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        command_execution_uuid = None
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                command_execution_uuid = CommandExecutionUUID.decode(reader, reader.read_uint32())
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.response = reader.read_bytes()
            else:
                reader.skip_type(tag & 7)

        if command_execution_uuid is None:
            msg = "Missing field 'commandExecutionUUID' in message 'ObservableCommandResponse'."
            raise DecodeError(msg, offset=reader.cursor)

        message.command_execution_uuid = command_execution_uuid

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        self.command_execution_uuid.encode(writer, 1)
        if self.response:
            writer.write_uint32(18).write_bytes(self.response)

        if number:
            writer.ldelim()

        return writer.finish()
