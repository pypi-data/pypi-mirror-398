import io
import textwrap

import typing_extensions as typing


class Serializer:
    """Serialize a python object into an xml stream."""

    def __init__(self, remove_whitespace: bool = False) -> None:
        self.indentation = 0
        self.buffer = io.StringIO()
        self.remove_whitespace = remove_whitespace

    @classmethod
    def serialize(cls, handler: typing.Callable[["Serializer"], None], /, *, remove_whitespace: bool = False) -> str:
        """
        Serialize an object using the given parsers into an XML string.

        Args:
          handler: The handler to serialize the root element
          remove_whitespace: Whether to omit whitespaces in the output.

        Returns:
          The string representation of the XML data.
        """

        serializer = Serializer(remove_whitespace)
        handler(serializer)

        return serializer.result()

    def result(self) -> str:
        """
        Return the result of the serializer.

        Returns:
          The serialized xml.
        """

        return self.buffer.getvalue()

    def start_element(self, name: str) -> typing.Self:
        """
        Write the start of an element with the given name.

        Args:
          name: The raw XML 1.0 name of the element type.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        self.write(f"<{name}>")
        self.indent()

        return self

    def end_element(self, name: str) -> typing.Self:
        """
        Write the end of an element with the given name.

        Args:
          name: The raw XML 1.0 name of the element type.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        self.dedent()
        self.write(f"</{name}>")

        return self

    def write_str(self, element: str, value: str, width: int = 88) -> typing.Self:
        """
        Write a string value surrounded by the given element.

        Args:
          element: The start and end element surrounding the string.
          value: The string value to write into the xml.
          width: The maximum length of characters per line. If the string
             exceeds this width, it is rendered in several lines.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        content = f"<{element}>"

        value = (
            value.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

        if len(value) > width:
            content += "\n"
            content += "\n".join(
                "\n".join(
                    textwrap.wrap(
                        line,
                        width,
                        initial_indent="  ",
                        subsequent_indent="  ",
                        break_long_words=False,
                        replace_whitespace=False,
                    )
                )
                for line in value.splitlines()
            )
            content += "\n"
        else:
            content += value

        content += f"</{element}>"

        return self.write(content)

    def write(self, value: str) -> typing.Self:
        """
        Write the value as a new line with the current indentation.

        Args:
          value: The value to write into the xml.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        buffer = textwrap.indent(
            value + ("\n" if not self.remove_whitespace else ""),
            "  " * (self.indentation if not self.remove_whitespace else 0),
        )

        self.buffer.write(buffer)

        return self

    def indent(self, level: int = 1) -> typing.Self:
        """
        Indent the upcoming lines.

        Args:
          level: By how many tabs to indent.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        self.indentation += level

        return self

    def dedent(self, level: int = 1) -> typing.Self:
        """
        Dedent the upcoming lines.

        Args:
          level: By how many tabs to dedent.

        Returns:
          The Serializer instance, allowing for method chaining.
        """

        self.indentation -= level

        return self
