import collections.abc
import dataclasses
import functools

import typing_extensions as typing

from ..common import Handler
from ..data_types import DataType, Element
from ..errors import DefinedExecutionError
from ..fdl import EndElement, Serializable, StartElement
from ..identifiers import CommandIdentifier
from ..validators import check_display_name, check_identifier

if typing.TYPE_CHECKING:
    from ..common import Feature
    from ..fdl import Deserializer, Serializer


@dataclasses.dataclass
class Command(Handler, Serializable):
    """Describes certain actions that can be performed on the server."""

    observable: bool = False
    """Whether the command execution is observable or not."""

    parameters: dict[str, "Element"] = dataclasses.field(default_factory=dict)
    """The parameters of the command."""

    responses: dict[str, "Element"] = dataclasses.field(default_factory=dict)
    """The responses of the command containing the result."""

    @functools.cached_property
    @typing.override
    def fully_qualified_identifier(self) -> CommandIdentifier:
        """Uniquely identifies the command."""

        return CommandIdentifier.create(**super().fully_qualified_identifier._data, command=self.identifier)

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.commands[self.identifier] = self

        return self

    @typing.override
    def serialize(self, serializer: "Serializer") -> None:
        from .observable_command import ObservableCommand

        serializer.start_element("Command")
        serializer.write_str("Identifier", self.identifier)
        serializer.write_str("DisplayName", self.display_name)
        serializer.write_str("Description", self.description)
        serializer.write_str("Observable", "Yes" if self.observable else "No")

        for element in self.parameters.values():
            serializer.start_element("Parameter")
            serializer.write_str("Identifier", element.identifier)
            serializer.write_str("DisplayName", element.display_name)
            serializer.write_str("Description", element.description)
            element.data_type.serialize(serializer)
            serializer.end_element("Parameter")

        for element in self.responses.values():
            serializer.start_element("Response")
            serializer.write_str("Identifier", element.identifier)
            serializer.write_str("DisplayName", element.display_name)
            serializer.write_str("Description", element.description)
            element.data_type.serialize(serializer)
            serializer.end_element("Response")

        if isinstance(self, ObservableCommand):
            for element in self.intermediate_responses.values():
                serializer.start_element("IntermediateResponse")
                serializer.write_str("Identifier", element.identifier)
                serializer.write_str("DisplayName", element.display_name)
                serializer.write_str("Description", element.description)
                element.data_type.serialize(serializer)
                serializer.end_element("IntermediateResponse")

        if self.errors:
            serializer.start_element("DefinedExecutionErrors")
            for Error in self.errors.values():
                serializer.write_str("Identifier", Error.identifier)
            serializer.end_element("DefinedExecutionErrors")

        serializer.end_element("Command")

    @typing.override
    @classmethod
    def deserialize(
        self, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        from .observable_command import ObservableCommand

        context = context or {}
        error_definitions: dict[str, type[DefinedExecutionError]] = context.get("error_definitions", {})

        yield from deserializer.read_start_element(name="Command")

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

        Factory = context["observable_command_factory"] if observable.value else context["unobservable_command_factory"]

        command = Factory(
            identifier=identifier.value,
            display_name=display_name.value,
            description=description.value,
        )

        while True:
            token = yield from deserializer.peek()
            if isinstance(token, EndElement):
                if token.name == "Command":
                    yield from deserializer.read_end_element(name="Command")

                break

            if isinstance(token, StartElement):
                if token.name == "DefinedExecutionErrors":
                    yield from deserializer.read_start_element(name="DefinedExecutionErrors")
                    while True:
                        errorToken = yield from deserializer.peek()

                        if isinstance(errorToken, EndElement) and errorToken.name == "DefinedExecutionErrors":
                            break

                        yield from deserializer.read_start_element(name="Identifier")
                        error = yield from deserializer.read_str()
                        check_identifier(error.value)
                        yield from deserializer.read_end_element(name="Identifier")

                        if error.value in error_definitions:
                            command.errors[error.value] = error_definitions[error.value]
                        else:
                            command.errors[error.value] = error_definitions[error.value] = DefinedExecutionError.create(
                                identifier=error.value, display_name=error.value
                            )

                    yield from deserializer.read_end_element(name="DefinedExecutionErrors")

                    continue

                if token.name == "Parameter":
                    yield from deserializer.read_start_element(name="Parameter")
                elif token.name == "Response":
                    yield from deserializer.read_start_element(name="Response")
                elif token.name == "IntermediateResponse":
                    yield from deserializer.read_start_element(name="IntermediateResponse")

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

                element = Element(
                    identifier=identifier.value,
                    display_name=display_name.value,
                    description=description.value,
                    data_type=data_type,
                )
                if token.name == "Parameter":
                    command.parameters[identifier.value] = element
                    yield from deserializer.read_end_element(name="Parameter")
                elif token.name == "Response":
                    command.responses[identifier.value] = element
                    yield from deserializer.read_end_element(name="Response")
                elif token.name == "IntermediateResponse":
                    if not isinstance(command, ObservableCommand):
                        msg = "IntermediateResponse can only be used with observable commands."
                        raise ValueError(msg)

                    command.intermediate_responses[identifier.value] = element
                    yield from deserializer.read_end_element(name="IntermediateResponse")

        return command
