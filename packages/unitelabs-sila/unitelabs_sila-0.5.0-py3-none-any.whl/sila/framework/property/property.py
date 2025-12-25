import collections.abc
import dataclasses
import functools

import typing_extensions as typing

from ..common import Handler
from ..data_types import Any, DataType
from ..errors import DefinedExecutionError
from ..fdl import EndElement, Serializable, StartElement
from ..identifiers import PropertyIdentifier
from ..validators import check_display_name, check_identifier

if typing.TYPE_CHECKING:
    from ..common import Feature
    from ..fdl import Deserializer, Serializer


@dataclasses.dataclass
class Property(Handler, Serializable):
    """Describes certain aspects of a server that do not require an action on the server."""

    observable: bool = False
    """Whether the property returns an observable stream or just a single value."""

    data_type: type["DataType"] = Any
    """The SiLA data type of the property."""

    @functools.cached_property
    @typing.override
    def fully_qualified_identifier(self) -> PropertyIdentifier:
        """Uniquely identifies the property."""

        return PropertyIdentifier.create(**super().fully_qualified_identifier._data, property=self.identifier)

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.properties[self.identifier] = self

        return self

    @typing.override
    def serialize(self, serializer: "Serializer") -> None:
        serializer.start_element("Property")
        serializer.write_str("Identifier", self.identifier)
        serializer.write_str("DisplayName", self.display_name)
        serializer.write_str("Description", self.description)
        serializer.write_str("Observable", "Yes" if self.observable else "No")
        self.data_type.serialize(serializer)
        if self.errors:
            serializer.start_element("DefinedExecutionErrors")
            for Error in self.errors.values():
                serializer.write_str("Identifier", Error.identifier)
            serializer.end_element("DefinedExecutionErrors")
        serializer.end_element("Property")

    @typing.override
    @classmethod
    def deserialize(
        self, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        context = context or {}
        error_definitions: dict[str, type[DefinedExecutionError]] = context.get("error_definitions", {})

        yield from deserializer.read_start_element(name="Property")

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

        yield from deserializer.read_start_element(name="Observable")
        observable = yield from deserializer.read_boolean()
        yield from deserializer.read_end_element(name="Observable")

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

        Factory = (
            context["observable_property_factory"] if observable.value else context["unobservable_property_factory"]
        )

        property_ = Factory(
            identifier=identifier.value,
            display_name=display_name.value,
            description=description.value,
            data_type=data_type,
            errors=errors,
        )

        yield from deserializer.read_end_element(name="Property")

        return property_
