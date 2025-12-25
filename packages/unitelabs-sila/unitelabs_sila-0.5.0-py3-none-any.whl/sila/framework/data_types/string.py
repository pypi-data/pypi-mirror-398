import dataclasses
import inspect

import typing_extensions as typing

from ..protobuf import Reader, WireType, Writer
from .data_type import BasicType

if typing.TYPE_CHECKING:
    from ..common import Context, Execution


@dataclasses.dataclass
class String(BasicType[str]):
    """
    Represents a plain text composed of maximum 2²¹ unicode characters.

    Use the SiLA binary type for larger data. It is recommended to
    specify a Constraint, e.g. a content-type or schema constraint
    for the SiLA string type in order to make the string content type
    safe.

    Attributes:
      value: The encapsulated `str` value. Defaults to an empty
        string.
    """

    value: str = ""

    @typing.override
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[str] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        if value is None:
            return await cls().validate()

        return await cls(value=value).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> str:
        await self.validate()

        return self.value

    @typing.override
    async def validate(self) -> typing.Self:
        if not isinstance(self.value, str):
            msg = f"Expected value of type 'str', received '{type(self.value).__name__}'."
            raise TypeError(msg)

        if len(self.value) > 2**21:
            msg = f"String must not exceed 2²¹ characters, received '{len(self.value)}'."
            raise ValueError(msg)

        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union["Reader", bytes], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                message.value = reader.read_string()
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.value:
            writer.write_uint32(10).write_string(self.value)

        if number:
            writer.ldelim()

        return writer.finish()

    @typing.override
    @classmethod
    def equals(cls, other: object) -> bool:
        return inspect.isclass(other) and issubclass(other, String)

    @typing.override
    def __str__(self) -> str:
        return self.value

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, String):
            return NotImplemented

        return self.value == other.value

    @typing.override
    def __hash__(self) -> int:
        return hash((self.value))
