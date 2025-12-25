import collections
import collections.abc
import dataclasses
import io
import textwrap
import xml.parsers
import xml.sax
import xml.sax.xmlreader

import typing_extensions as typing

from .parse_error import ParseError

if typing.TYPE_CHECKING:
    from ..data_types import Boolean, Date, Integer, Real, String, Time, Timestamp

T = typing.TypeVar("T")
T_co = typing.TypeVar("T_co", covariant=True)
S = typing.TypeVar("S")


@dataclasses.dataclass
class Token:
    """Represents a token in the xml stream."""


@dataclasses.dataclass
class StartElement(Token):
    """Represents a start element in the xml stream."""

    name: str
    attrs: dict[str, str] = dataclasses.field(compare=False, default_factory=dict)


@dataclasses.dataclass
class EndElement(Token):
    """Represents an end element in the xml stream."""

    name: str


@dataclasses.dataclass
class Characters(Token):
    """Represents a characters in the xml stream."""

    value: list[str]


@dataclasses.dataclass
class EndDocument(Token):
    """Represents the end of the xml stream."""


class Handler(typing.Protocol[T_co]):
    """Handler for deserializing an xml stream."""

    def __call__(  # noqa: D102
        self, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, T_co]: ...


class Deserializer(xml.sax.ContentHandler, xml.sax.ErrorHandler, typing.Generic[T]):
    """Deserialize an xml stream into a python object."""

    def __init__(self, content: str = "", context: typing.Optional[dict] = None):
        super().__init__()

        self.running = False
        self.content = content
        self.context = context or {}
        self._names: list[str] = []
        self._result: typing.Optional[T] = None
        self._exception: typing.Optional[BaseException] = None
        self._locator: typing.Optional[xml.sax.xmlreader.Locator] = None
        self._tokens: list[Token] = []
        self._characters: list[str] = []
        self._handlers = collections.deque[collections.abc.Generator[None, typing.Any, typing.Any]]()

    @classmethod
    def deserialize(cls, content: str, handler: Handler[T], context: typing.Optional[dict] = None) -> T:
        """
        Deserialize the given XML string using the given handler.

        Args:
          content: The string representation of the XML data.
          handler: The handler to deserialize the root element.
          context: The deserialization context for the handler.

        Returns:
          The parsed object.

        Raises:
          ParseError: If unexpected or invalid data is detected during
            parsing.
        """

        deserializer = cls(content, context)
        deserializer.register(handler(deserializer, context))
        parser = xml.sax.make_parser()
        parser.setContentHandler(deserializer)
        parser.setErrorHandler(deserializer)
        parser.forbid_dtd = True  # type: ignore
        parser.forbid_entities = True  # type: ignore
        parser.forbid_external = True  # type: ignore

        stream = io.StringIO(content.strip())
        parser.parse(stream)

        return deserializer.result()

    def done(self) -> bool:
        """Whether the deserializer has a result or an exception set."""

        return self._result is not None or self._exception is not None

    def result(self) -> T:
        """
        Get the result of the deserializer.

        Returns:
          The result value.

        Raises:
          RuntimeError: If the deserializer's result isn't yet available.
          BaseException: If the deserializer is done and has an exception
            set by the `set_exception()` method.
        """

        if self._exception is not None:
            raise self._exception

        if self._result is None:
            msg = "Result is not set."
            raise RuntimeError(msg)

        return self._result

    def set_result(self, result: T) -> None:
        """
        Mark the deserializer as done and set its result.

        Args:
          result: The result to set.
        """

        self._result = result

    def set_exception(self, exception: BaseException) -> None:
        """
        Mark the deserializer as done and set an exception.

        Args:
          exception: The exception to raise.
        """

        self._exception = exception

    def read_start_element(self, name: str) -> collections.abc.Generator[None, Token, StartElement]:
        """
        Expect the start of an element with the given name.

        Args:
          name: Contains the raw XML 1.0 name of the element type.

        Yields:
          The detected start element.

        Raises:
          ValueError: If the expected and detected tokens differ.
        """

        if self._tokens:
            token = self._tokens.pop()
        else:
            token = yield

        if not isinstance(token, StartElement):
            if isinstance(token, EndElement):
                msg = f"Expected start element with name '{name}', received end element with name '{token.name}'."
                raise ValueError(msg)

            if isinstance(token, Characters):
                msg = f"Expected start element with name '{name}', received characters '{token.value}'."
                raise ValueError(msg)

            msg = f"Expected start element with name '{name}', received token '{token}'."
            raise ValueError(msg)

        if token.name != name:
            msg = f"Expected start element with name '{name}', received start element with name '{token.name}'."
            raise ValueError(msg)

        return token

    def read_end_element(self, name: str) -> collections.abc.Generator[None, Token, EndElement]:
        """
        Expect the end of an element with the given name.

        Args:
          name: Contains the raw XML 1.0 name of the element type.

        Yields:
          The detected end element.

        Raises:
          ValueError: If the expected and detected tokens differ.
        """

        if self._tokens:
            token = self._tokens.pop()
        else:
            token = yield

        if not isinstance(token, EndElement):
            if isinstance(token, StartElement):
                msg = f"Expected end element with name '{name}', received start element with name '{token.name}'."
                raise ValueError(msg)

            if isinstance(token, Characters):
                msg = f"Expected end element with name '{name}', received characters '{token.value}'."
                raise ValueError(msg)

            msg = f"Expected end element with name '{name}', received token '{token}'."
            raise ValueError(msg)

        if token.name != name:
            msg = f"Expected end element with name '{name}', received end element with name '{token.name}'."
            raise ValueError(msg)

        return token

    def read_str(self) -> collections.abc.Generator[None, Token, "String"]:
        """
        Read a string value from the buffer.

        Returns:
          The string value read from the xml.
        """

        token = yield from self.read_characters()
        token = textwrap.dedent("".join(token.value)).strip()
        token = (
            token.replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&quot;", '"')
            .replace("&apos;", "'")
        )

        from ..data_types import String

        return String(token)

    def read_boolean(self) -> collections.abc.Generator[None, Token, "Boolean"]:
        """
        Read a `Boolean` value from the buffer.

        Returns:
          The `Boolean` value read from the xml.
        """

        value = yield from self.read_str()

        if value.value not in ("Yes", "No"):
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Boolean."
            raise ValueError(msg)

        from ..data_types import Boolean

        return Boolean(value.value == "Yes")

    def read_integer(self) -> collections.abc.Generator[None, Token, "Integer"]:
        """
        Read an `Integer` value from the buffer.

        Returns:
          The `Integer` value read from the xml.
        """

        value = yield from self.read_str()

        try:
            from ..data_types import Integer

            return Integer(int(value.value))
        except ValueError:
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Integer."
            raise ValueError(msg) from None

    def read_float(self) -> collections.abc.Generator[None, Token, "Real"]:
        """
        Read a `Real` value from the buffer.

        Returns:
          The `Real` value read from the xml.
        """

        value = yield from self.read_str()

        try:
            from ..data_types import Real

            return Real(float(value.value))
        except ValueError:
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Real."
            raise ValueError(msg) from None

    def read_date(self) -> collections.abc.Generator[None, Token, "Date"]:
        """
        Read a `Date` value from the buffer.

        Returns:
          The `Date` value read from the xml.
        """

        value = yield from self.read_str()

        try:
            from ..data_types import Date

            return Date.from_isoformat(value.value)
        except ValueError:
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Date."
            raise ValueError(msg) from None

    def read_time(self) -> collections.abc.Generator[None, Token, "Time"]:
        """
        Read a `Time` value from the buffer.

        Returns:
          The `Time` value read from the xml.
        """

        value = yield from self.read_str()

        try:
            from ..data_types import Time

            return Time.from_isoformat(value.value)
        except ValueError:
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Time."
            raise ValueError(msg) from None

    def read_timestamp(self) -> collections.abc.Generator[None, Token, "Timestamp"]:
        """
        Read a `Timestamp` value from the buffer.

        Returns:
          The `Timestamp` value read from the xml.
        """

        value = yield from self.read_str()

        try:
            from ..data_types import Timestamp

            return Timestamp.from_isoformat(value.value)
        except ValueError:
            msg = f"Could not convert '{self._names[-1]}' with value '{value.value}' to Timestamp."
            raise ValueError(msg) from None

    def read_characters(self) -> collections.abc.Generator[None, Token, Characters]:
        """
        Expect chunks of characters.

        Yields:
          The detected chunks of characters.

        Raises:
          ValueError: If the expected and detected tokens differ.
        """

        if self._tokens:
            token = self._tokens.pop()
        else:
            token = yield

        if not isinstance(token, Characters):
            if isinstance(token, StartElement):
                msg = f"Expected characters, received start element with name '{token.name}'."
                raise ValueError(msg)
            if isinstance(token, EndElement):
                self._tokens.append(token)
                return Characters(value=[])

            msg = f"Expected characters, received token '{token}'."
            raise ValueError(msg)

        return token

    def peek(self) -> collections.abc.Generator[None, typing.Any, Token]:
        """
        Look ahead one item without advancing the iterator.

        Returns:
          The token that will be next returned from `read()`.
        """

        token = yield

        self._tokens.append(token)

        return token

    def read(
        self, handler: typing.Optional[Handler[S]] = None, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, S]:
        """
        Expect to read elements in the order defined in the given handler.

        Args:
          handler: The handler used to continue deserialization.
          context: The deserialization context for the handler.

        Returns:
          The deserialized object returned by the handler.

        Raises:
          ParseError: If the expected and detected tokens differ.
        """

        if handler is not None:
            context = {**self.context, **(context or {})}
            self.register(handler(self, context))

        token = yield

        return token

    @typing.override
    def startDocument(self) -> None:
        """Signals the beginning of a document."""

        self.running = True

    @typing.override
    def endDocument(self) -> None:
        """Signals the end of a document."""

        self.running = False
        while self._handlers:
            self.__handle_token(EndDocument())

    @typing.override
    def startElement(self, name: str, attrs: typing.Optional[xml.sax.xmlreader.AttributesImpl] = None) -> None:
        """
        Signals the start of an element in non-namespace mode.

        Args:
          name: Contains the raw XML 1.0 name of the element type.
          attrs: Contains the attributes of the element.
        """

        self._names.append(name)

        if not self._handlers:
            msg = f"Received start element with name '{name}', but no handler registered."
            raise ValueError(msg)

        self.__handle_token(StartElement(name, dict(attrs.items()) if attrs is not None else {}))

    @typing.override
    def endElement(self, name: str) -> None:
        """
        Signals the end of an element in non-namespace mode.

        Args:
          name: Contains the raw XML 1.0 name of the element type.
        """

        if not self._handlers:
            msg = f"Received end element with name '{name}', but no handler registered."
            raise ValueError(msg)

        if not self._names:
            msg = f"Did not expect an end element, received end element with name '{name}'."
            raise ValueError(msg)

        if self._names[-1] != name:
            msg = f"Expected end element with name '{self._names[-1]}', received end element with name '{name}'."
            raise ValueError(msg)

        self.__handle_token(EndElement(name))
        self._names.pop()

    @typing.override
    def characters(self, content: str) -> None:
        """
        Receive notification of character data.

        Args:
          content: A chunk of character data.
        """

        if content.strip() or self._characters:
            self._characters.append(content)

    @typing.override
    def setDocumentLocator(self, locator: xml.sax.xmlreader.Locator) -> None:
        """
        Receive access to a locator of document events.

        Args:
          locator: Allows for locating the origin of document events.
        """

        self._locator = locator

    @typing.override
    def error(self, exception: BaseException) -> typing.NoReturn:
        """
        Handle a recoverable error.

        Args:
          exception: The error to handle.
        """

        if not isinstance(exception, ParseError):
            exception = ParseError(
                exception.args[0],
                path=self._names,
                line=self._locator.getLineNumber() or 0 if self._locator is not None else 0,
                column=self._locator.getColumnNumber() or 0 if self._locator is not None else 0,
            )

        self.set_exception(exception)

        raise exception

    @typing.override
    def fatalError(self, exception: BaseException) -> typing.NoReturn:
        """
        Handle a non-recoverable error.

        Args:
          exception: The fatal error to handle.
        """

        self.error(exception)

    def register(self, handler: collections.abc.Generator[None, typing.Any, typing.Any]) -> None:
        """
        Register a handler and advance it to its first yield.

        Args:
          handler: A generator that receives and processes token through
            yield statements.
        """

        self._handlers.append(handler)

        try:
            next(handler)
        except Exception as error:  # noqa: BLE001
            self.error(error)

    def __handle_token(self, token: Token) -> None:
        if self._characters:
            characters = Characters(self._characters)
            self._characters = []

            self.__handle_token(characters)

        try:
            self._handlers[-1].send(token)
        except StopIteration as result:
            self._handlers.pop().close()

            if self._handlers:
                self.__handle_token(result.value)
            else:
                self.set_result(result.value)
        except Exception as error:  # noqa: BLE001
            self.error(error)
