import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class CreateBinaryRequest(Message):
    """
    Initiate the process of transferring binary data in chunks.

    Attributes:
      binary_size: The total size of the binary data to be
        transferred, in bytes.
      chunk_count: The total number of chunks that the binary data
        will be divided into for transfer.
      parameter_identifier: A unique identifier for the parameter
        associated with this binary data transfer.
    """

    binary_size: int = 0
    chunk_count: int = 0
    parameter_identifier: str = ""

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
                reader.expect_type(tag, WireType.VARINT)
                message.chunk_count = reader.read_uint32()
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message.parameter_identifier = reader.read_string()
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
        if self.chunk_count:
            writer.write_uint32(16).write_uint32(self.chunk_count)
        if self.parameter_identifier:
            writer.write_uint32(26).write_string(self.parameter_identifier)

        if number:
            writer.ldelim()

        return writer.finish()
