import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer
from .cloud_metadata import CloudMetadata


@dataclasses.dataclass
class PropertyRequest(Message):
    """
    Read or subscribe a SiLA property.

    Attributes:
      fully_qualified_property_id: The fully qualified identifier of
        the property to read or subscribe to.
      metadata: A list of SiLA client metadata, if any.
    """

    fully_qualified_property_id: str = ""
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
                message.fully_qualified_property_id = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                size = reader.read_uint32()
                value = CloudMetadata.decode(reader.buffer[reader.cursor : reader.cursor + size])
                message.metadata.append(value)
                reader.skip(size)
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.fully_qualified_property_id:
            writer.write_uint32(10).write_string(self.fully_qualified_property_id)

        for metadata in self.metadata:
            metadata.encode(writer, 2)

        if number:
            writer.ldelim()

        return writer.finish()
