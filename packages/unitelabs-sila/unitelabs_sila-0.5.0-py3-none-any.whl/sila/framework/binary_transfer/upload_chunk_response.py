import dataclasses

import typing_extensions as typing

from ..data_types import Duration
from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class UploadChunkResponse(Message):
    """
    Acknowledges the successful upload of a specific chunk.

    Attributes:
      binary_transfer_uuid: A unique identifier (UUID) for the binary
        transfer session to which the chunk was uploaded.
      chunk_index: The sequential index of the chunk that was
        successfully uploaded.
      lifetime_of_binary: The remaining duration for which the binary
        data will be retained on the server before it expires.
    """

    binary_transfer_uuid: str = ""
    chunk_index: int = 0
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
                message.chunk_index = reader.read_uint32()
            elif field_number == 3:
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
        if self.chunk_index:
            writer.write_uint32(16).write_uint32(self.chunk_index)
        self.lifetime_of_binary.encode(writer, 3)

        if number:
            writer.ldelim()

        return writer.finish()
