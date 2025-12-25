import collections.abc
import dataclasses
import inspect

import typing_extensions as typing

from ..fdl import Deserializer, Serializer
from .data_type import BasicType, DataType
from .string import String

if typing.TYPE_CHECKING:
    from ..common import Context, Execution
    from ..fdl import Serializer
    from ..protobuf import Reader, Writer


@dataclasses.dataclass
class Void(BasicType):
    """Represents no data as a value of the SiLA any type."""

    @typing.override
    @classmethod
    async def from_native(
        cls, context: "Context", value: None = None, /, *, execution: typing.Optional["Execution"] = None
    ) -> typing.Self:
        return await cls().validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> None:
        await self.validate()

        return

    @typing.override
    async def validate(self) -> typing.Self:
        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union["Reader", bytes], length: typing.Optional[int] = None) -> typing.Self:
        return cls()

    @typing.override
    def encode(self, writer: typing.Optional["Writer"] = None, number: typing.Optional[int] = None) -> bytes:
        return b"\x0a\x00"

    @typing.override
    @classmethod
    def serialize(cls, serializer: "Serializer") -> None:
        serializer.start_element("DataType")
        serializer.start_element("Constrained")
        serializer.start_element("DataType")
        serializer.write_str("Basic", "String")
        serializer.end_element("DataType")
        serializer.start_element("Constraints")
        serializer.write_str("Length", "0")
        serializer.end_element("Constraints")
        serializer.end_element("Constrained")
        serializer.end_element("DataType")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type["Void"]]:
        from ..constraints import Length

        yield from deserializer.read_start_element(name="Constrained")
        data_type = yield from deserializer.read(DataType.deserialize)
        assert data_type is String

        yield from deserializer.read_start_element(name="Constraints")
        yield from deserializer.read(Length.deserialize, {"data_type": data_type})
        yield from deserializer.read_end_element("Constraints")
        yield from deserializer.read_end_element(name="Constrained")

        return cls

    @typing.override
    @classmethod
    def equals(cls, other: object) -> bool:
        return inspect.isclass(other) and issubclass(other, Void)

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Void):
            return NotImplemented

        return True

    @typing.override
    def __hash__(self) -> int:
        return hash(None)
