import dataclasses

import typing_extensions as typing

from ..data_types import Duration
from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class DownloadChunkResponse(Message):
    """
    The requested chunk of binary data, along with its metadata.

    Attributes:
      binary_transfer_uuid: A unique identifier (UUID) for the binary
        transfer session from which the chunk was retrieved.
      offset: The starting byte position within the binary data from
        which this chunk was retrieved.
      payload: The actual binary data chunk retrieved from the
        transfer session.
      lifetime_of_binary: The remaining duration for which the binary
        data will be retained on the server before it expires.
    """

    binary_transfer_uuid: str = ""
    offset: int = 0
    payload: bytes = b""
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
                reader.expect_type(tag, WireType.LEN)
                message.binary_transfer_uuid = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.VARINT)
                message.offset = reader.read_uint64()
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message.payload = reader.read_bytes()
            elif field_number == 4:
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

        if self.binary_transfer_uuid:
            writer.write_uint32(10).write_string(self.binary_transfer_uuid)
        if self.offset:
            writer.write_uint32(16).write_uint64(self.offset)
        if self.payload:
            writer.write_uint32(26).write_bytes(self.payload)
        self.lifetime_of_binary.encode(writer, 4)

        if number:
            writer.ldelim()

        return writer.finish()
