import builtins
import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.binary import Binary
from ..data_types.string import String
from ..fdl import Characters, Deserializer, EndElement, Serializer, StartElement
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List

T = typing.TypeVar("T", String, Binary)


class ContentTypeParameter(typing.NamedTuple):
    """Represents a parameter for the content type, consisting of an attribute and its corresponding value."""

    attribute: str
    """The name of the parameter attribute, e.g. 'charset'."""

    value: str
    """The value of the parameter attribute, e.g. 'utf-8'."""


@dataclasses.dataclass(init=False)
class ContentType(Constraint[T]):
    """A constraint that defines a media type (content type) with optional parameters."""

    Parameter: typing.ClassVar[builtins.type[ContentTypeParameter]] = ContentTypeParameter
    """
    Represents a parameter for the content type, consisting of an
    attribute and its corresponding value.
    """

    type: str
    """The main type of the content (e.g., 'application', 'text')."""

    subtype: str
    """The subtype of the content (e.g., 'json', 'html')."""

    parameters: list[ContentTypeParameter] = dataclasses.field(default_factory=list)
    """
    A set of additional parameters for the content type (e.g.,
    'charset' or 'boundary').
    """

    @property
    def media_type(self) -> str:
        """
        The full media type string.

        Includes the type, subtype, and any additional parameters in the
        format 'type/subtype; param=value'.
        """

        return f"{self.type}/{self.subtype}" + "".join(
            [f"; {parameter[0]}={parameter[1]}" for parameter in self.parameters]
        )

    def __init__(
        self,
        ctype: str,
        subtype: str,
        parameters: typing.Optional[
            collections.abc.Sequence[typing.Union[ContentTypeParameter, tuple[str, str]]]
        ] = None,
    ) -> None:
        self.type = ctype
        self.subtype = subtype
        self.parameters = [
            parameter
            if isinstance(parameter, ContentTypeParameter)
            else ContentTypeParameter(parameter[0], parameter[1])
            for parameter in parameters or []
        ]

    @typing.override
    async def validate(self, value: T) -> bool:
        if not isinstance(value, (String, Binary)):
            msg = f"Expected value of type 'String' or 'Binary', received '{type(value).__name__}'."
            raise TypeError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.start_element("ContentType")
        serializer.write_str("Type", self.type)
        serializer.write_str("Subtype", self.subtype)

        if len(self.parameters):
            serializer.start_element("Parameters")
            for parameter in self.parameters:
                serializer.start_element("Parameter")
                serializer.write_str("Attribute", parameter.attribute)
                serializer.write_str("Value", parameter.value)
                serializer.end_element("Parameter")
            serializer.end_element("Parameters")

        serializer.end_element("ContentType")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, (String, Binary)):
            msg = f"Expected constraint's data type to be 'String' or 'Binary', received '{data_type.__name__}'."
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="ContentType")

        # Type
        yield from deserializer.read_start_element(name="Type")
        ctype = yield from deserializer.read_str()
        yield from deserializer.read_end_element(name="Type")

        # Subtype
        yield from deserializer.read_start_element(name="Subtype")
        subtype = yield from deserializer.read_str()
        yield from deserializer.read_end_element(name="Subtype")

        token = yield

        if isinstance(token, StartElement):
            if token.name != "Parameters":
                msg = f"Expected start element with name 'Parameters', received start element with name '{token.name}'."
                raise ValueError(msg)

        elif isinstance(token, Characters):
            msg = (
                f"Expected start element with name 'Parameters' or end element with name 'ContentType', "
                f"received characters '{token.value}'."
            )
            raise ValueError(msg)

        elif isinstance(token, EndElement) and token.name == "ContentType":
            return cls(ctype.value, subtype.value)

        parameters: list[ContentTypeParameter] = []
        while True:
            token = yield

            if isinstance(token, StartElement):
                if token.name == "Parameter":
                    # Attribute
                    yield from deserializer.read_start_element(name="Attribute")
                    attribute = yield from deserializer.read_str()
                    yield from deserializer.read_end_element(name="Attribute")

                    # Value
                    yield from deserializer.read_start_element(name="Value")
                    value = yield from deserializer.read_str()
                    yield from deserializer.read_end_element(name="Value")

                    parameters.append(ContentTypeParameter(attribute.value, value.value))

                else:
                    msg = (
                        f"Expected start element with name 'Parameter', "
                        f"received start element with name '{token.name}'."
                    )
                    raise ValueError(msg)

            elif isinstance(token, EndElement):
                if token.name == "Parameter":
                    continue
                else:
                    break  # pragma: no cover

            elif isinstance(token, Characters):
                msg = f"Expected start element with name 'Parameter', received characters '{token.value}'."
                raise ValueError(msg)

        if not parameters:
            msg = "Expected at least one 'Parameter' element inside the 'ContentType' element."
            raise ValueError(msg)

        yield from deserializer.read_end_element(name="ContentType")

        return cls(ctype.value, subtype.value, parameters)
