import collections.abc
import dataclasses
import functools
import weakref

import typing_extensions as typing

from ..common import Execution
from ..data_types import Any, Convertable, Native
from ..errors import DefinedExecutionError, InvalidMetadata
from ..fdl import EndElement, Serializable, StartElement
from ..identifiers import MetadataIdentifier
from ..protobuf import ConversionError, DecodeError, Message
from ..validators import check_display_name, check_identifier

if typing.TYPE_CHECKING:
    from ..common import Context, Feature, Handler
    from ..data_types import DataType
    from ..fdl import Deserializer, Serializer

T = typing.TypeVar("T", bound=Native)


@dataclasses.dataclass
class Metadata(Message, Serializable, Convertable[T], typing.Generic[T]):
    """
    Additional information the server expects to receive from a client.

    Attributes:
      identifier: Uniquely identifies the metadata within the scope
        of the same feature.
      display_name: Human readable name of the metadata.
      description: Describes the use and purpose of the metadata.
      data_type: The SiLA data type of the metadata.
      errors: The list of defined execution errors that may occur
        when handling this metadata.
      affects: The list of calls affected by this metadata.
      feature: The SiLA feature this metadata was registered with.
      value: The metadata type instance.
    """

    identifier: typing.ClassVar[str] = ""
    display_name: typing.ClassVar[str] = ""
    description: typing.ClassVar[str] = ""
    data_type: typing.ClassVar[type["DataType"]] = Any
    errors: typing.ClassVar[dict[str, type["DefinedExecutionError"]]] = {}
    affects: typing.ClassVar[collections.abc.Sequence[str]] = []
    feature: typing.ClassVar[typing.Optional["Feature"]] = None

    value: "DataType" = dataclasses.field(default_factory=Any)

    @classmethod
    async def from_buffer(
        cls, context: "Handler", metadata: typing.Optional[dict[str, bytes]] = None, /
    ) -> typing.Self:
        """
        Convert a buffer value to its corresponding SiLA metadata.

        Args:
          context: The handler the metadata is associated with.
          metadata: The received metadata dictionary.

        Returns:
          An instance of the corresponding SiLA metadata.

        Raises:
          InvalidMetadata: If the provided buffer cannot be converted to
            the SiLA metadata.
        """

        assert context.feature

        metadata = metadata or {}
        rpc_header = cls.rpc_header()

        if rpc_header not in metadata or not (metadatum := metadata[rpc_header]):
            msg = f"Missing metadata '{cls.identifier}' in {context.__class__.__name__} '{context.identifier}'."
            raise InvalidMetadata(msg)

        try:
            return cls.decode(metadatum)
        except DecodeError as error:
            msg = (
                f"Unable to decode metadata '{cls.identifier}' in "
                f"{context.__class__.__name__} '{context.identifier}': {error.message}"
            )
            raise InvalidMetadata(msg) from None

    @classmethod
    @typing.override
    async def from_native(
        cls, context: "Context", value: typing.Optional[T] = None, /, *, execution: typing.Optional["Execution"] = None
    ) -> typing.Self:
        return cls(await cls.data_type.from_native(context, value, execution=execution))

    @typing.override
    async def to_native(self, context: "Context", /) -> T:
        try:
            return await self.value.to_native(context)
        except ConversionError as error:
            msg = f"Unable to decode metadata '{self.identifier}': {error.message}"
            raise InvalidMetadata(msg) from None

    @classmethod
    @functools.cache
    def fully_qualified_identifier(cls) -> MetadataIdentifier:
        """Uniquely identifies the metadata."""

        if cls.feature is None:
            msg = (
                f"Unable to get fully qualified identifier for Metadata '{cls.identifier}' without feature association."
            )
            raise RuntimeError(msg)

        return MetadataIdentifier.create(**cls.feature.fully_qualified_identifier._data, metadata=cls.identifier)

    @classmethod
    @functools.cache
    def rpc_header(cls) -> str:
        """Get the gRPC header specifier used to identify metadata."""

        return f"sila-{cls.fully_qualified_identifier().lower().replace('/', '-')}-bin"

    @typing.override
    @classmethod
    def serialize(cls, serializer: "Serializer") -> None:
        serializer.start_element("Metadata")
        serializer.write_str("Identifier", cls.identifier)
        serializer.write_str("DisplayName", cls.display_name)
        serializer.write_str("Description", cls.description)
        cls.data_type.serialize(serializer)
        if cls.errors:
            serializer.start_element("DefinedExecutionErrors")
            for Error in cls.errors.values():
                serializer.write_str("Identifier", Error.identifier)
            serializer.end_element("DefinedExecutionErrors")
        serializer.end_element("Metadata")

    @typing.override
    @classmethod
    def deserialize(
        self, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        from ..data_types import DataType

        context = context or {}
        error_definitions: dict[str, type[DefinedExecutionError]] = context.get("error_definitions", {})

        yield from deserializer.read_start_element(name="Metadata")

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

        errors_token = yield from deserializer.peek()

        errors: dict[str, type[DefinedExecutionError]] = {}
        if isinstance(errors_token, StartElement) and errors_token.name == "DefinedExecutionErrors":
            yield from deserializer.read_start_element("DefinedExecutionErrors")

            while True:
                errors_token = yield from deserializer.peek()
                if isinstance(errors_token, EndElement) and errors_token.name == "DefinedExecutionErrors":
                    break

                yield from deserializer.read_start_element("Identifier")
                error = yield from deserializer.read_str()
                check_identifier(error.value)
                yield from deserializer.read_end_element("Identifier")

                if error.value in error_definitions:
                    errors[error.value] = error_definitions[error.value]
                else:
                    errors[error.value] = error_definitions[error.value] = DefinedExecutionError.create(
                        identifier=error.value, display_name=error.value
                    )

            yield from deserializer.read_end_element("DefinedExecutionErrors")

        Factory = context["metadata_factory"]

        metadata = Factory.create(
            identifier=identifier.value,
            display_name=display_name.value,
            description=description.value,
            data_type=data_type,
            errors=errors,
        )

        yield from deserializer.read_end_element(name="Metadata")

        return metadata

    @classmethod
    def add_to_feature(cls, feature: "Feature") -> type[typing.Self]:
        """
        Register this metadata with a feature.

        Args:
          feature: The feature to add this metadata to.

        Returns:
          The class, allowing for method chaining.
        """

        cls.feature = weakref.proxy(feature)
        feature.metadata[cls.identifier] = cls
        for error in cls.errors.values():
            error.add_to_feature(feature)

        return cls

    @classmethod
    def create(
        cls,
        identifier: str,
        display_name: str,
        description: str = "",
        data_type: type["DataType"] = Any,
        errors: typing.Optional[collections.abc.Mapping[str, type["DefinedExecutionError"]]] = None,
        affects: typing.Optional[collections.abc.Sequence[str]] = None,
        feature: typing.Optional["Feature"] = None,
        **kwargs,
    ) -> type[typing.Self]:
        """
        Create a new SiLA `Metadata` class with the provided data type.

        Args:
          identifier: Uniquely identifies the metadata within the scope
            of the same feature.
          display_name: Human readable name of the metadata.
          description: Describes the use and purpose of the metadata.
          data_type: The SiLA data type for the metadata value.
          errors: A list of defined execution errors that can happen when
            accessing this handler.
          affects: A list of handlers affected by this metadata.
          feature: The feature the metadata is assigned to.
          name: An optional name for the new `Metadata` class.

        Returns:
          A new `Metadata` class with the specified data type.
        """

        check_identifier(identifier)
        check_display_name(display_name)

        metadata: type[typing.Self] = dataclasses.make_dataclass(
            identifier or cls.__name__,
            [("value", data_type, dataclasses.field(default_factory=data_type))],
            bases=(cls,),
            namespace={
                "__doc__": description,
                "identifier": identifier,
                "display_name": display_name,
                "description": description,
                "data_type": data_type,
                "errors": dict(errors or {}),
                "affects": list(affects or []),
                "feature": feature,
                **kwargs,
            },
            eq=False,
        )

        if feature is not None:
            metadata.add_to_feature(feature)

        return metadata

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Metadata):
            return NotImplemented

        return (
            self.identifier == other.identifier
            and self.display_name == other.display_name
            and self.description == other.description
            and self.data_type.__name__ == other.data_type.__name__
            and self.errors == other.errors
            and self.affects == other.affects
            and self.value == other.value
        )

    __hash__ = None
