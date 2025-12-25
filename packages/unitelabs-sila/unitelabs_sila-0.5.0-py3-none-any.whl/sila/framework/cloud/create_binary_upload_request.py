import dataclasses

import typing_extensions as typing

from ..binary_transfer import CreateBinaryRequest
from ..protobuf import Message, Reader, WireType, Writer
from .cloud_metadata import CloudMetadata


@dataclasses.dataclass
class CreateBinaryUploadRequest(Message):
    """
    Initiate the process of transferring binary data in chunks.

    Attributes:
      create_binary_request: The binary creation request.
      metadata: A list of SiLA client metadata, if any.
    """

    create_binary_request: CreateBinaryRequest = dataclasses.field(default_factory=CreateBinaryRequest)
    metadata: list[CloudMetadata] = dataclasses.field(default_factory=list)

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
                size = reader.read_uint32()
                value = CloudMetadata.decode(reader.buffer[reader.cursor : reader.cursor + size])
                message.metadata.append(value)
                reader.skip(size)
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.create_binary_request = CreateBinaryRequest.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        for metadata in self.metadata:
            metadata.encode(writer, 1)

        self.create_binary_request.encode(writer, 2)

        if number:
            writer.ldelim()

        return writer.finish()
