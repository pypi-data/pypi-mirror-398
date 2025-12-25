import abc
import collections.abc

import typing_extensions as typing

from ..fdl import Deserializer, EndElement, Serializable, Serializer, StartElement
from ..protobuf import Message
from .convertable import Convertable, T

if typing.TYPE_CHECKING:
    from ..common import Context, Execution


class DataType(Message, Convertable[T], Serializable, typing.Generic[T], metaclass=abc.ABCMeta):
    """The data type of any information exchanged between SiLA server and client."""

    @typing.override
    @classmethod
    @abc.abstractmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[T] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self: ...

    @typing.override
    @abc.abstractmethod
    async def to_native(self, context: "Context", /) -> T: ...

    @typing.override
    @abc.abstractmethod
    async def validate(self) -> typing.Self: ...

    @typing.override
    @classmethod
    @abc.abstractmethod
    def serialize(cls, serializer: Serializer) -> None: ...

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type["DataType"]]:
        from ..data_types import Constrained, Custom, List, Structure

        yield from deserializer.read_start_element(name="DataType")

        token = yield from deserializer.peek()

        if isinstance(token, StartElement):
            if token.name == "Basic":
                data_type = yield from deserializer.read(BasicType.deserialize)
            elif token.name == "List":
                data_type = yield from deserializer.read(List.deserialize)
            elif token.name == "Structure":
                data_type = yield from deserializer.read(Structure.deserialize)
            elif token.name == "Constrained":
                data_type = yield from deserializer.read(Constrained.deserialize)
            elif token.name == "DataTypeIdentifier":
                data_type = yield from deserializer.read(Custom.deserialize)
            else:
                msg = (
                    f"Expected start element with name 'Basic', 'List', 'Structure', 'Constrained' "
                    f"or 'DataTypeIdentifier', received start element with name '{token.name}'."
                )
                raise ValueError(msg)
        elif isinstance(token, EndElement):
            msg = (
                f"Expected start element with name 'Basic', 'List', 'Structure', 'Constrained' or "
                f"'DataTypeIdentifier', received end element with name '{token.name}'."
            )
            raise ValueError(msg)
        else:
            msg = (
                f"Expected start element with name 'Basic', 'List', 'Structure', 'Constrained' or "
                f"'DataTypeIdentifier', received token '{token}'."
            )
            raise ValueError(msg)

        yield from deserializer.read_end_element(name="DataType")

        return data_type

    @classmethod
    @abc.abstractmethod
    def equals(cls, other: object) -> bool:
        """Compare this data type with another data type."""


class BasicType(typing.Generic[T], DataType[T]):
    """A predefined collection of SiLA data types without any child data type items."""

    @typing.override
    @classmethod
    def serialize(cls, serializer: Serializer) -> None:
        serializer.start_element("DataType")
        serializer.write_str("Basic", cls.__name__)
        serializer.end_element("DataType")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type["BasicType"]]:
        from ..data_types import Any, Binary, Boolean, Date, Integer, Real, String, Time, Timestamp

        yield from deserializer.read_start_element("Basic")

        basic_type = yield from deserializer.read_str()

        yield from deserializer.read_end_element("Basic")

        if basic_type.value == "String":
            return String
        elif basic_type.value == "Integer":
            return Integer
        elif basic_type.value == "Real":
            return Real
        elif basic_type.value == "Boolean":
            return Boolean
        elif basic_type.value == "Binary":
            return Binary
        elif basic_type.value == "Date":
            return Date
        elif basic_type.value == "Time":
            return Time
        elif basic_type.value == "Timestamp":
            return Timestamp
        elif basic_type.value == "Any":
            return Any
        else:
            msg = f"Expected basic type value, received '{basic_type.value}'."
            raise ValueError(msg)
