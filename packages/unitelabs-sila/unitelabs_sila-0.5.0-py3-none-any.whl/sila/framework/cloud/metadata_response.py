import dataclasses

import typing_extensions as typing

from ..protobuf import Message, Reader, WireType, Writer


@dataclasses.dataclass
class MetadataResponse(Message):
    """
    Response with calls affected by the requested metadata.

    Attributes:
      affected_calls: The list of calls affected by the requested
        metadata.
    """

    affected_calls: list[str] = dataclasses.field(default_factory=list)

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
                message.affected_calls.append(reader.read_string())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        for affected_call in self.affected_calls:
            writer.write_uint32(10).write_string(affected_call)

        if number:
            writer.ldelim()

        return writer.finish()
