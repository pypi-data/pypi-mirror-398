import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class MetadataRequest(Message):
    """
    Message the get calls affected by the given metadata.

    Attributes:
      fully_qualified_metadata_id: The fully qualified identifier of
        the metadata to get the affected calls for.
    """

    fully_qualified_metadata_id: str = ""

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
                message.fully_qualified_metadata_id = reader.read_string()
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.fully_qualified_metadata_id:
            writer.write_uint32(10).write_string(self.fully_qualified_metadata_id)

        if number:
            writer.ldelim()

        return writer.finish()
