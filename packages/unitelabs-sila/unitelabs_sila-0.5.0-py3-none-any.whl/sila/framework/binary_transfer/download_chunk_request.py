import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class DownloadChunkRequest(Message):
    """
    Download a specific chunk of binary data.

    Attributes:
      binary_transfer_uuid: A unique identifier (UUID) for the binary
        transfer session from which the chunk is being requested.
      offset: The starting byte position within the binary data from
        which to begin retrieving the chunk.
      length: The number of bytes to retrieve starting from the
        offset position.
    """

    binary_transfer_uuid: str = ""
    offset: int = 0
    length: int = 0

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
                reader.expect_type(tag, WireType.VARINT)
                message.length = reader.read_uint32()
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
        if self.length:
            writer.write_uint32(24).write_uint32(self.length)

        if number:
            writer.ldelim()

        return writer.finish()
