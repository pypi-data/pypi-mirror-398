import dataclasses
import enum

import typing_extensions as typing

from ..data_types import Duration, Real
from ..protobuf import Message, Reader, WireType, Writer


class CommandExecutionStatus(enum.IntEnum):
    """Provides details about the execution status of a command."""

    WAITING = 0
    """The command is waiting for its execution."""

    RUNNING = 1
    """The command is currently executing."""

    FINISHED_SUCCESSFULLY = 2
    """The command finished successfully."""

    FINISHED_WITH_ERROR = 3
    """The command finished with an error."""


@dataclasses.dataclass
class CommandExecutionInfo(Message):
    """Provides information about the current status of a Command being executed."""

    Status: typing.ClassVar[type[CommandExecutionStatus]] = CommandExecutionStatus

    status: CommandExecutionStatus = CommandExecutionStatus.WAITING
    """The current status of the execution of a command."""

    progress: typing.Optional[Real] = None
    """The estimated progress of a command execution in percent (0 - 100%)."""

    remaining_time: typing.Optional[Duration] = None
    """The estimated remaining execution time of the command."""

    updated_lifetime: typing.Optional[Duration] = None
    """The duration during which a command execution UUID is valid."""

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
                reader.expect_type(tag, WireType.VARINT)
                message.status = CommandExecutionStatus(reader.read_int32())
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.progress = Real.decode(reader, reader.read_uint32())
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message.remaining_time = Duration.decode(reader, reader.read_uint32())
            elif field_number == 4:
                reader.expect_type(tag, WireType.LEN)
                message.updated_lifetime = Duration.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.status:
            writer.write_uint32(8).write_int32(self.status)
        if self.progress:
            self.progress.encode(writer, 2)
        if self.remaining_time:
            self.remaining_time.encode(writer, 3)
        if self.updated_lifetime:
            self.updated_lifetime.encode(writer, 4)

        if number:
            writer.ldelim()

        return writer.finish()
