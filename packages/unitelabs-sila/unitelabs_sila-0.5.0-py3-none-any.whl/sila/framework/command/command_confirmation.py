import dataclasses

import typing_extensions as typing

from ..data_types import Duration
from ..protobuf import DecodeError, Message, Reader, WireType, Writer
from .command_execution_uuid import CommandExecutionUUID


@dataclasses.dataclass
class CommandConfirmation(Message):
    """
    A command confirmation message is returned to identify the command execution.

    Attributes:
      command_execution_uuid: The unique identifier of a command
        execution. It is unique within one instance of a SiLA server
        and its lifetime.
      lifetime_of_execution: The duration during which a command
        execution UUID is valid. The lifetime of execution is always
        a relative duration with respect to the point in time the
        SiLA server initiated the response to the SiLA client.
    """

    command_execution_uuid: CommandExecutionUUID = dataclasses.field(default_factory=CommandExecutionUUID)
    lifetime_of_execution: typing.Optional[Duration] = None

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
                message.lifetime_of_execution = Duration.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        if command_execution_uuid is None:
            msg = "Missing field 'commandExecutionUUID' in message 'CommandConfirmation'."
            raise DecodeError(msg, offset=reader.cursor)

        message.command_execution_uuid = command_execution_uuid

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        self.command_execution_uuid.encode(writer, 1)
        if self.lifetime_of_execution is not None:
            self.lifetime_of_execution.encode(writer, 2)

        if number:
            writer.ldelim()

        return writer.finish()
