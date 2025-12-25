import collections.abc
import dataclasses
import functools
import inspect

import typing_extensions as typing

from ..fdl import Deserializer, Serializer
from ..identifiers import DataTypeIdentifier
from ..protobuf import DecodeError, Reader, WireType, Writer
from ..validators import check_display_name, check_identifier
from .any import Any
from .constrained import Constrained
from .convertable import Native
from .data_type import DataType
from .list import List

if typing.TYPE_CHECKING:
    from ..common import Context, Execution, Feature

T = typing.TypeVar("T", bound=Native)


@dataclasses.dataclass
class Custom(DataType[T]):
    """
    A user-defined data type that can be used through other data types.

    Attributes:
      identifier: Uniquely identifies the custom data type within the
        scope of the same feature.
      display_name: Human readable name of the custom data type.
      description: Describes the use and purpose of the custom data
        type.
      data_type: The SiLA data type of the custom data type.
      value: The custom SiLA data type instance.
    """

    identifier: typing.ClassVar[str] = ""
    display_name: typing.ClassVar[str] = ""
    description: typing.ClassVar[str] = ""
    data_type: typing.ClassVar[type[DataType]] = Any
    feature: typing.ClassVar[typing.Optional["Feature"]] = None

    value: DataType = dataclasses.field(default_factory=Any)

    @classmethod
    @functools.cache
    def fully_qualified_identifier(cls) -> DataTypeIdentifier:
        """Uniquely identifies the custom data type definition."""

        if cls.feature is None:
            msg = (
                f"Unable to get fully qualified identifier for Custom Data Type "
                f"'{cls.identifier}' without feature association."
            )
            raise RuntimeError(msg)

        return DataTypeIdentifier.create(**cls.feature.fully_qualified_identifier._data, data_type=cls.identifier)

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
        return await cls(value=await cls.data_type.from_native(context, value, execution=execution)).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> T:
        await self.validate()

        return await self.value.to_native(context)

    @typing.override
    async def validate(self) -> typing.Self:
        if not isinstance(self.value, self.data_type):
            msg = f"Expected value of type '{self.data_type.__name__}', received '{type(self.value).__name__}'."
            raise TypeError(msg)

        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        flag = False
        message = cls()
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            pos = reader.cursor
            tag = reader.read_uint32()

            if tag >> 3 == 1:
                reader.expect_type(tag, WireType.LEN)

                try:
                    if issubclass(cls.data_type, List) or (
                        issubclass(cls.data_type, Constrained) and issubclass(cls.data_type.data_type, List)
                    ):
                        if not flag:
                            message.value = cls.data_type.decode(reader.buffer[pos:end])
                            flag = True

                        reader.skip_type(tag & 7)
                    else:
                        message.value = message.value.decode(reader, reader.read_uint32())
                except DecodeError as error:
                    msg = f"Invalid field '{cls.identifier}' in message '{cls.__name__}': {error.message}"
                    raise DecodeError(msg, error.offset, [cls.identifier, *error.path]) from None

            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        self.value.encode(writer, 1)

        if number:
            writer.ldelim()

        return writer.finish()

    @typing.override
    @classmethod
    def serialize(cls, serializer: Serializer, *, definition: bool = False) -> None:
        if definition:
            serializer.start_element("DataTypeDefinition")
            serializer.write_str("Identifier", cls.identifier)
            serializer.write_str("DisplayName", cls.display_name)
            serializer.write_str("Description", cls.description)
            cls.data_type.serialize(serializer)
            serializer.end_element("DataTypeDefinition")
        else:
            serializer.start_element("DataType")
            serializer.write_str("DataTypeIdentifier", cls.identifier)
            serializer.end_element("DataType")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type[typing.Self]]:
        context = context or {}
        definition = context.get("definition", False)
        data_type_definitions: dict[str, type[Custom]] = context.get("data_type_definitions", {})

        if definition:
            yield from deserializer.read_start_element(name="DataTypeDefinition")

            yield from deserializer.read_start_element(name="Identifier")
            identifier = yield from deserializer.read_str()
            check_identifier(identifier.value)
            yield from deserializer.read_end_element(name="Identifier")

            yield from deserializer.read_start_element(name="DisplayName")
            display_name = yield from deserializer.read_str()
            check_display_name(display_name.value)
            yield from deserializer.read_end_element(name="DisplayName")

            yield from deserializer.read_start_element(name="Description")
            description = yield from deserializer.read_str()
            yield from deserializer.read_end_element(name="Description")

            data_type = yield from deserializer.read(DataType.deserialize)
            yield from deserializer.read_end_element(name="DataTypeDefinition")

            if identifier.value in data_type_definitions:
                data_type_definitions[identifier.value].display_name = display_name.value
                data_type_definitions[identifier.value].description = description.value
                data_type_definitions[identifier.value].data_type = data_type

                return data_type_definitions[identifier.value]

            data_type_definitions[identifier.value] = cls.create(
                identifier.value, display_name.value, description.value, data_type
            )

            return data_type_definitions[identifier.value]
        else:
            yield from deserializer.read_start_element(name="DataTypeIdentifier")

            identifier = yield from deserializer.read_str()
            check_identifier(identifier.value)

            yield from deserializer.read_end_element(name="DataTypeIdentifier")

            if identifier.value not in data_type_definitions:
                data_type_definitions[identifier.value] = cls.create(
                    identifier=identifier.value, display_name=identifier.value
                )

            return data_type_definitions[identifier.value]

    @classmethod
    def add_to_feature(cls, feature: "Feature") -> type[typing.Self]:
        """
        Register this custom data type with a feature.

        Args:
          feature: The feature to add this custom data type to.

        Returns:
          The class, allowing for method chaining.
        """

        feature.data_type_definitions[cls.identifier] = cls

        return cls

    @classmethod
    def create(
        cls,
        identifier: str,
        display_name: str,
        description: str = "",
        data_type: type[DataType] = Any,
        feature: typing.Optional["Feature"] = None,
        name: typing.Optional[str] = None,
    ) -> type[typing.Self]:
        """
        Create a new SiLA `Custom` class with the provided data type.

        Args:
          identifier: Uniquely identifies the custom data type within the
            scope of the same feature.
          display_name: Human readable name of the custom data type.
          description: Describes the use and purpose of the custom data
            type.
          data_type: The SiLA data type for the custom value.
          feature: The feature the custom data type is assigned to.
          name: An optional name for the new `Custom` class.

        Returns:
          A new `Custom` class with the specified data type.
        """

        check_identifier(identifier)
        check_display_name(display_name)

        custom: type[typing.Self] = dataclasses.make_dataclass(
            name or identifier or cls.__name__,
            [("value", data_type, dataclasses.field(default_factory=data_type))],
            bases=(cls,),
            namespace={
                "__doc__": description,
                "identifier": identifier,
                "display_name": display_name,
                "description": description,
                "data_type": data_type,
                "feature": feature,
            },
            eq=False,
        )

        if feature is not None:
            custom.add_to_feature(feature)

        return custom

    @typing.override
    @classmethod
    def equals(cls, other: object) -> bool:
        if not inspect.isclass(other) or not issubclass(other, Custom):
            return False

        return (
            cls.identifier == other.identifier
            and cls.display_name == other.display_name
            and cls.description == other.description
            and cls.data_type.equals(other.data_type)
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Custom):
            return NotImplemented

        return type(self).equals(type(other)) and self.value == other.value

    __hash__ = None
