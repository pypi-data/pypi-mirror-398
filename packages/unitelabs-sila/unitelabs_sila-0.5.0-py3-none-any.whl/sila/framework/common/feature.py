import collections.abc
import dataclasses
import functools

import typing_extensions as typing

from ..fdl import EndElement, Serializable, StartElement
from ..identifiers import FeatureIdentifier
from ..validators import check_display_name, check_identifier
from .context_proxy import ContextProxy

if typing.TYPE_CHECKING:
    from ..command import Command
    from ..data_types import Custom
    from ..errors import DefinedExecutionError
    from ..fdl import Deserializer, Serializer
    from ..metadata import Metadata
    from ..property import Property
    from .context import Context


@dataclasses.dataclass
class Feature(Serializable):
    """Describes a specific behavior of a SiLA server."""

    locale: str = dataclasses.field(default="en-us")
    """The locale for the feature."""

    sila2_version: str = dataclasses.field(default="1.1")
    """The SiLA2 version for the feature."""

    version: str = dataclasses.field(default="1.0")
    """The version of the feature."""

    maturity_level: typing.Literal["Draft", "Verified", "Normative"] = dataclasses.field(default="Draft")
    """The maturity level of the feature."""

    originator: str = dataclasses.field(default="org.silastandard")
    """The originator of the feature."""

    category: str = dataclasses.field(default="none")
    """The category of the feature."""

    identifier: str = ""
    """
    Uniquely identifies the feature within the scope of the same
    originator and category.
    """

    display_name: str = ""
    """Human readable name of the feature."""

    description: str = dataclasses.field(default="")
    """Description of the behavior and capability of the feature."""

    commands: dict[str, "Command"] = dataclasses.field(default_factory=dict)
    """The commands associated with the feature."""

    properties: dict[str, "Property"] = dataclasses.field(default_factory=dict)
    """The properties associated with the feature."""

    metadata: dict[str, type["Metadata"]] = dataclasses.field(default_factory=dict)
    """The metadata associated with the feature."""

    errors: dict[str, type["DefinedExecutionError"]] = dataclasses.field(default_factory=dict)
    """The errors associated with the feature."""

    data_type_definitions: dict[str, type["Custom"]] = dataclasses.field(default_factory=dict)
    """The custom data type definitions associated with the feature."""

    context: "Context" = dataclasses.field(compare=False, default_factory=ContextProxy)
    """The context (either client or server) the feature was registered with."""

    def __post_init__(self) -> None:
        check_identifier(self.identifier)
        check_display_name(self.display_name)

        for command in self.commands.values():
            command.feature = self

        for property_ in self.properties.values():
            property_.feature = self

        for metadata in self.metadata.values():
            metadata.add_to_feature(self)

    @functools.cached_property
    def fully_qualified_identifier(self) -> FeatureIdentifier:
        """Uniquely identifies the feature."""

        return FeatureIdentifier.create(
            self.originator, self.category, self.identifier, int(self.version.rpartition(".")[0])
        )

    @functools.cached_property
    def rpc_package(self) -> str:
        """The package specifier to namespace services and protobuf messages."""

        return ".".join(
            (
                "sila2",
                self.originator,
                self.category,
                str(self.identifier).lower(),
                f"v{self.version.rpartition('.')[0]}",
            )
        )

    @typing.override
    def serialize(self, serializer: "Serializer") -> None:
        serializer.write('<?xml version="1.0" encoding="utf-8" ?>')

        attrs = {
            "Locale": self.locale if self.locale != "en-us" else None,
            "SiLA2Version": self.sila2_version,
            "FeatureVersion": self.version,
            "MaturityLevel": self.maturity_level if self.maturity_level != "Draft" else None,
            "Originator": self.originator,
            "Category": self.category if self.category != "none" else None,
        }
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items() if v is not None)
        serializer.write(
            f"<Feature {attr_str}\n"
            '         xmlns="http://www.sila-standard.org"\n'
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '         xsi:schemaLocation="http://www.sila-standard.org https://gitlab.com/SiLA2/sila_base/raw/master/schema/FeatureDefinition.xsd">'
        )
        serializer.indent()
        serializer.write_str("Identifier", self.identifier)
        serializer.write_str("DisplayName", self.display_name)
        serializer.write_str("Description", self.description)

        for command in self.commands.values():
            command.serialize(serializer)

        for property_ in self.properties.values():
            property_.serialize(serializer)

        for metadata in self.metadata.values():
            metadata.serialize(serializer)

        for Error in self.errors.values():
            Error.serialize(serializer)

        for DataTypeDefinition in self.data_type_definitions.values():
            DataTypeDefinition.serialize(serializer, definition=True)

        serializer.end_element("Feature")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        from ..command import Command
        from ..data_types import Custom
        from ..errors import DefinedExecutionError
        from ..metadata import Metadata
        from ..property import Property

        feature_element = yield from deserializer.read_start_element(name="Feature")

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

        feature = cls(
            identifier=identifier.value,
            display_name=display_name.value,
            description=description.value,
            originator=feature_element.attrs.get("Originator", "org.silastandard"),
            category=feature_element.attrs.get("Category", "none"),
            maturity_level=feature_element.attrs.get("MaturityLevel", "Draft"),
            version=feature_element.attrs.get("FeatureVersion", "1.0"),
            sila2_version=feature_element.attrs.get("SiLA2Version", "1.1"),
            locale=feature_element.attrs.get("Locale", "en-us"),
        )

        while True:
            token = yield from deserializer.peek()

            if isinstance(token, StartElement):
                if token.name == "Command":
                    command = yield from deserializer.read(Command.deserialize)
                    command.add_to_feature(feature)

                if token.name == "Property":
                    property_ = yield from deserializer.read(Property.deserialize)
                    property_.add_to_feature(feature)

                if token.name == "Metadata":
                    metadata = yield from deserializer.read(Metadata.deserialize)
                    metadata.add_to_feature(feature)

                if token.name == "DefinedExecutionError":
                    error = yield from deserializer.read(DefinedExecutionError.deserialize)
                    error.add_to_feature(feature)

                if token.name == "DataTypeDefinition":
                    data_type_definition: type[Custom] = yield from deserializer.read(
                        Custom.deserialize, {"definition": True}
                    )
                    data_type_definition.add_to_feature(feature)

            if isinstance(token, EndElement):
                yield from deserializer.read_end_element("Feature")
                break

        return feature

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Feature):
            return NotImplemented

        return other.fully_qualified_identifier == self.fully_qualified_identifier

    __hash__ = None
