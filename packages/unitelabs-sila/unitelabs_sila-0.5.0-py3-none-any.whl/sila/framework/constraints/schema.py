import builtins
import collections.abc
import dataclasses
import enum
import functools
import importlib.resources
import io
import json
import socket
import urllib.error
import urllib.request
import warnings

import jsonschema
import jsonschema.exceptions
import typing_extensions as typing
import xmlschema

from ..data_types.binary import Binary
from ..data_types.string import String
from ..fdl import Characters, Deserializer, EndElement, Serializer, StartElement
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List

T = typing.TypeVar("T", String, Binary)


class UnavailableSchema(Exception):
    """Exception raised when a schema is not available."""


class SchemaType(str, enum.Enum):
    """
    Enumeration of schema types used in the Schema constraint.

    This enumeration defines the types of schemas that can be used
    for validation. It currently supports XML and JSON.
    """

    XML = "Xml"
    """Represents the XML schema type."""

    JSON = "Json"
    """Represents the JSON schema type."""


@dataclasses.dataclass
class Schema(Constraint[T]):
    """A constraint that enforces the structure of a value to match a specific schema, either XML or JSON."""

    Type: typing.ClassVar[builtins.type[SchemaType]] = SchemaType
    """
    Enumeration of schema types used in the Schema constraint.
    """

    type: typing.Union[typing.Literal["Xml", "Json"], SchemaType]
    """
    The schema type, either 'Xml' or 'Json'.
    """

    url: typing.Optional[str] = None
    """
    An optional URL pointing to the schema.
    """

    inline: typing.Optional[str] = None
    """
    Optional inline content representing the schema.
    """

    def __post_init__(self):
        if self.url is None and self.inline is None:
            msg = "Either 'url' or 'inline' must be provided."
            raise ValueError(msg)

        if self.url is not None and self.inline is not None:
            msg = "'url' and 'inline' cannot both be provided."
            raise ValueError(msg)

        self.type = self.type.value if isinstance(self.type, SchemaType) else self.type
        self._validator = self.get_validator()

    @typing.override
    async def validate(self, value: T) -> bool:
        if not isinstance(value, (String, Binary)):
            msg = f"Expected value of type 'String' or 'Binary', received '{type(value).__name__}'."
            raise TypeError(msg)

        if self._validator is None:
            self._validator = self.get_validator()

        if self._validator is None:
            return True

        content = value.value
        if isinstance(content, bytes):
            content = content.decode("utf-8")

        if self.type == SchemaType.JSON:
            content = json.loads(content)

        try:
            self._validator(content)
        except xmlschema.XMLSchemaException as error:
            msg = f"Failed to validate xml value against schema: {error}."
            raise ValueError(msg) from error
        except jsonschema.exceptions.ValidationError as error:
            msg = f"Failed to validate json value against schema: {error.message}."
            raise ValueError(msg) from error

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.start_element("Schema")
        serializer.write_str("Type", self.type)
        if self.url is not None:
            serializer.write_str("Url", self.url)
        if self.inline is not None:
            serializer.write_str("Inline", self.inline)
        serializer.end_element("Schema")

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

        yield from deserializer.read_start_element(name="Schema")

        # Type
        yield from deserializer.read_start_element(name="Type")
        schema_type = yield from deserializer.read_str()
        try:
            schema_type = SchemaType(schema_type.value).value
        except ValueError:
            msg = f"Expected a valid 'Type' value, received '{schema_type}'."
            raise ValueError(msg) from None
        yield from deserializer.read_end_element(name="Type")

        url: typing.Optional[String] = None
        inline: typing.Optional[String] = None

        token = yield
        if isinstance(token, StartElement):
            if token.name == "Url":
                # Url
                url = yield from deserializer.read_str()
                yield from deserializer.read_end_element(name="Url")
            elif token.name == "Inline":
                # Inline
                inline = yield from deserializer.read_str()
                yield from deserializer.read_end_element(name="Inline")
            else:
                msg = (
                    f"Expected start element with name 'Url' or 'Inline', "
                    f"received start element with name '{token.name}'."
                )
                raise ValueError(msg)
        elif isinstance(token, Characters):
            msg = f"Expected start element with name 'Url' or 'Inline', received characters '{token.value}'."
            raise ValueError(msg)
        elif isinstance(token, EndElement):
            msg = f"Expected start element with name 'Url' or 'Inline', received end element with name '{token.name}'."
            raise ValueError(msg)

        yield from deserializer.read_end_element(name="Schema")

        return cls(
            schema_type, url=url.value if url is not None else None, inline=inline.value if inline is not None else None
        )

    def get_validator(self) -> typing.Optional[typing.Callable[[str], None]]:
        """
        Get a validator for the schema.

        Returns:
          A validator for the schema or `None` if the schema is not
          available.

        Raises:
          ValueError: If the schema is available but not valid.
        """

        try:
            if self.type == SchemaType.XML:
                return self.get_xml_validator()

            if self.type == SchemaType.JSON:
                return self.get_json_validator()
        except UnavailableSchema as error:
            msg = f"Skipping schema validation due to unreachable url '{self.url}': {error}."
            warnings.warn(msg, stacklevel=2)
            return None

        msg = f"Schema constraint received unsupported schema type: '{self.type}'."
        raise ValueError(msg)

    def get_xml_validator(self) -> typing.Callable[[str], None]:
        """
        Get a xml validator for the schema.

        Returns:
          A xml validator for the schema.

        Raises:
          UnavailableSchema: If the schema is not available.
          ValueError: If the schema is available but not valid.
        """

        resources = importlib.resources.files("sila") / "resources"
        if (
            self.url is not None
            and "gitlab.com/sila2/sila_base" in self.url.lower()
            and (filename := self.url.split("/")[-1])
            and (resources / filename).is_file()
        ):
            return xmlschema.XMLSchema(resources / filename, base_url=resources).validate

        try:
            schema = io.StringIO(self.inline) if self.inline is not None else self.url
            return xmlschema.XMLSchema(schema).validate
        except xmlschema.exceptions.XMLResourceOSError as error:
            msg = f"{str(error).rpartition(':')[2].strip()}"
            raise UnavailableSchema(msg) from error
        except xmlschema.XMLSchemaException as error:
            msg = f"Failed to parse xml schema: {error}."
            raise ValueError(msg) from error

    def get_json_validator(self) -> typing.Callable[[str], None]:
        """
        Get a json validator for the schema.

        Returns:
          A json validator for the schema,

        Raises:
          UnavailableSchema: If the schema is not available.
          ValueError: If the schema is available but not valid.
        """

        schema = self.inline

        if self.url is not None:
            try:
                with urllib.request.urlopen(self.url, timeout=1) as response:
                    data: bytes = response.read()
            except (socket.timeout, urllib.error.URLError) as error:
                msg = "Connection timed out" if isinstance(error, socket.timeout) else error.reason
                raise UnavailableSchema(msg) from error
            else:
                schema = data.decode("utf-8")

        try:
            schema: dict = json.loads(schema)
        except json.JSONDecodeError as error:
            msg = f"Failed to parse json schema: {error.msg}."
            raise ValueError(msg) from error

        return functools.partial(jsonschema.validate, schema=schema)
