import collections.abc
import dataclasses
import inspect

import typing_extensions as typing

from ..fdl import Deserializer, Serializer
from ..protobuf import ConversionError, DecodeError, Reader, WireType, Writer
from .any import Any
from .convertable import Native
from .data_type import BasicType, DataType

if typing.TYPE_CHECKING:
    from ..common import Context, Execution
    from .constrained import Constrained
    from .custom import Custom
    from .structure import Structure

T = typing.TypeVar("T", bound=list[Native])


@dataclasses.dataclass
class List(DataType[T]):
    """
    An ordered list with entries of the same SiLA data type.

    Attributes:
      data_type: The SiLA data type of each list item.
      value: The list of SiLA data type instances.
    """

    data_type: typing.ClassVar[type[typing.Union[BasicType, "Structure", "Constrained", "Custom"]]] = Any

    value: collections.abc.Sequence[typing.Union[BasicType, "Structure", "Constrained", "Custom"]] = dataclasses.field(
        default_factory=list
    )

    @typing.override
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[T] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        value = value or []

        values = []
        for index, item in enumerate(value):
            try:
                values.append(await cls.data_type.from_native(context, item, execution=execution))
            except ConversionError as error:
                raise ConversionError(error.message, [index, *error.path]) from error
            except Exception as error:  # noqa: BLE001
                raise ConversionError(str(error), [index]) from None

        return await cls(value=values).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> T:
        await self.validate()

        values: T = typing.cast(T, [])
        for index, item in enumerate(self.value):
            if not isinstance(item, self.data_type):
                msg = f"Expected value of type '{self.data_type.__name__}', received '{type(item).__name__}'."
                raise ConversionError(msg, [index])

            try:
                values.append(await item.to_native(context))
            except ConversionError as error:
                raise ConversionError(error.message, [index, *error.path]) from error
            except Exception as error:  # noqa: BLE001
                raise ConversionError(str(error), [index]) from None

        return values

    @typing.override
    async def validate(self) -> typing.Self:
        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        end = reader.length if length is None else reader.cursor + length

        values = []
        field_number = 0
        while reader.cursor < end:
            tag = reader.read_uint32()

            if field_number == 0:
                field_number = tag >> 3
            elif field_number != tag >> 3:
                reader.skip_type(tag & 7)
                continue

            try:
                reader.expect_type(tag, WireType.LEN)
                value = message.data_type.decode(reader, reader.read_uint32())
                values.append(value)
            except DecodeError as error:
                raise DecodeError(error.message, error.offset, [len(values), *error.path]) from None

        message.value = values

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        for item in self.value:
            item.encode(writer, number or 1)

        return writer.finish()

    @typing.override
    @classmethod
    def serialize(cls, serializer: Serializer) -> None:
        serializer.start_element("DataType")
        serializer.start_element("List")
        cls.data_type.serialize(serializer)
        serializer.end_element("List")
        serializer.end_element("DataType")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type[typing.Self]]:
        from .constrained import Constrained
        from .custom import Custom
        from .structure import Structure

        yield from deserializer.read_start_element(name="List")

        data_type = yield from deserializer.read(DataType.deserialize)

        if issubclass(data_type, cls):
            msg = "The data type of list entries must not be a list itself."
            raise ValueError(msg)

        assert (
            issubclass(data_type, BasicType)
            or issubclass(data_type, Structure)
            or issubclass(data_type, Constrained)
            or issubclass(data_type, Custom)
        )

        yield from deserializer.read_end_element(name="List")

        return cls.create(data_type)

    @classmethod
    def create(
        cls,
        data_type: type[typing.Union[BasicType, "Structure", "Constrained", "Custom"]] = Any,
        name: str = "",
    ) -> type[typing.Self]:
        """
        Create a new SiLA `List` class with the provided data type.

        Args:
          data_type: The SiLA data type of each list item.
          name: An optional name for the new `List` class.

        Returns:
          A new `List` class with the specified data type.
        """

        from .constrained import Constrained

        if issubclass(data_type, List) or (
            issubclass(data_type, Constrained) and issubclass(data_type.data_type, List)
        ):
            msg = "The data type of list entries must not be a list itself."
            raise TypeError(msg)

        return dataclasses.make_dataclass(
            name or cls.__name__,
            [("value", collections.abc.Sequence[data_type], dataclasses.field(default_factory=list))],
            bases=(cls,),
            namespace={"data_type": data_type},
            eq=False,
        )

    @typing.override
    @classmethod
    def equals(cls, other: object) -> bool:
        if not inspect.isclass(other) or not issubclass(other, List):
            return False

        return cls.data_type.equals(other.data_type)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, List):
            return NotImplemented

        return (
            type(self).equals(type(other))
            and len(self.value) == len(other.value)
            and all(a == b for a, b in zip(self.value, other.value))
        )

    __hash__ = None
