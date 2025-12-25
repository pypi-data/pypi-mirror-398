import dataclasses

import typing_extensions as typing

from ..data_types import Duration
from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class GetBinaryInfoResponse(Message):
    """
    The detailed info about a specific binary transfer session.

    Attributes:
      binary_size: The total size of the binary data associated with
        the transfer session, in bytes.
      lifetime_of_binary: The remaining duration for which the binary
        data will be retained on the server before it expires.
    """

    binary_size: int = 0
    lifetime_of_binary: Duration = dataclasses.field(default_factory=Duration)

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
                message.binary_size = reader.read_uint64()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.lifetime_of_binary = Duration.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.binary_size:
            writer.write_uint32(8).write_uint64(self.binary_size)
        self.lifetime_of_binary.encode(writer, 2)

        if number:
            writer.ldelim()

        return writer.finish()
