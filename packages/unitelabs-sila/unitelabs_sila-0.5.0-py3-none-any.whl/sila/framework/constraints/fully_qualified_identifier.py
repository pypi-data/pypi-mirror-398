import collections.abc
import dataclasses
import enum

import typing_extensions as typing

from ..data_types.string import String
from ..fdl import Deserializer, Serializer
from ..identifiers import (
    CommandIdentifier,
    DataTypeIdentifier,
    ErrorIdentifier,
    FeatureIdentifier,
    IntermediateResponseIdentifier,
    MetadataIdentifier,
    ParameterIdentifier,
    PropertyIdentifier,
    ResponseIdentifier,
)
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List


class Identifier(str, enum.Enum):
    """Enum representing various SiLA identifier types."""

    FEATURE_IDENTIFIER = "FeatureIdentifier"
    """Identifier for a feature."""

    COMMAND_IDENTIFIER = "CommandIdentifier"
    """Identifier for a command."""

    COMMAND_PARAMETER_IDENTIFIER = "CommandParameterIdentifier"
    """Identifier for a command parameter."""

    COMMAND_RESPONSE_IDENTIFIER = "CommandResponseIdentifier"
    """Identifier for a command response."""

    INTERMEDIATE_COMMAND_RESPONSE_IDENTIFIER = "IntermediateCommandResponseIdentifier"
    """Identifier for an intermediate command response."""

    DEFINED_EXECUTION_ERROR_IDENTIFIER = "DefinedExecutionErrorIdentifier"
    """Identifier for a defined execution error."""

    PROPERTY_IDENTIFIER = "PropertyIdentifier"
    """Identifier for a property."""

    DATA_TYPE_IDENTIFIER = "TypeIdentifier"
    """Identifier for a custom data type."""

    METADATA_IDENTIFIER = "MetadataIdentifier"
    """Identifier for metadata."""


@dataclasses.dataclass
class FullyQualifiedIdentifier(Constraint[String]):
    """
    A constraint that enforces a Fully Qualified Identifier for a `String` value.

    Raises:
      ValueError: If `value` is not a valid Fully Qualified Identifier.
    """

    Type: typing.ClassVar[type[Identifier]] = Identifier
    """Enum representing various SiLA identifier types."""

    value: typing.Union[
        typing.Literal[
            "FeatureIdentifier",
            "CommandIdentifier",
            "CommandParameterIdentifier",
            "CommandResponseIdentifier",
            "IntermediateCommandResponseIdentifier",
            "DefinedExecutionErrorIdentifier",
            "PropertyIdentifier",
            "TypeIdentifier",
            "MetadataIdentifier",
        ],
        Identifier,
    ]
    """
    The specific identifier type (e.g., 'FeatureIdentifier',
    'CommandIdentifier', etc.) that the string must match.
    """

    def __post_init__(self):
        self.value = self.value.value if isinstance(self.value, Identifier) else self.value

        try:
            self.__validate = {
                Identifier.FEATURE_IDENTIFIER: FeatureIdentifier,
                Identifier.COMMAND_IDENTIFIER: CommandIdentifier,
                Identifier.COMMAND_PARAMETER_IDENTIFIER: ParameterIdentifier,
                Identifier.COMMAND_RESPONSE_IDENTIFIER: ResponseIdentifier,
                Identifier.INTERMEDIATE_COMMAND_RESPONSE_IDENTIFIER: IntermediateResponseIdentifier,
                Identifier.DEFINED_EXECUTION_ERROR_IDENTIFIER: ErrorIdentifier,
                Identifier.PROPERTY_IDENTIFIER: PropertyIdentifier,
                Identifier.DATA_TYPE_IDENTIFIER: DataTypeIdentifier,
                Identifier.METADATA_IDENTIFIER: MetadataIdentifier,
            }[Identifier(self.value)]
        except ValueError:
            msg = f"Identifier type must be valid type, received '{self.value}'."
            raise ValueError(msg) from None

    @typing.override
    async def validate(self, value: String) -> bool:
        if not isinstance(value, String):
            msg = f"Expected value of type 'String', received '{type(value).__name__}'."
            raise TypeError(msg)

        try:
            self.__validate(value.value)
        except Exception:  # noqa: BLE001
            msg = f"Expected value with format for a '{self.value}', received '{value}'."
            raise ValueError(msg) from None

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.write_str("FullyQualifiedIdentifier", self.value)

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, String):
            msg = f"Expected constraint's data type to be 'String', received '{data_type.__name__}'."
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="FullyQualifiedIdentifier")
        value = yield from deserializer.read_str()
        try:
            value = Identifier(value.value).value
        except ValueError:
            msg = f"Expected a valid 'FullyQualifiedIdentifier' value, received '{value}'."
            raise ValueError(msg) from None
        yield from deserializer.read_end_element(name="FullyQualifiedIdentifier")

        return cls(value)
