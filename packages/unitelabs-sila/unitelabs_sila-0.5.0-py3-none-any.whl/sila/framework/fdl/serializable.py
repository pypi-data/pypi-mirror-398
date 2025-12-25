import collections.abc

import typing_extensions as typing

if typing.TYPE_CHECKING:
    from .deserializer import Deserializer
    from .serializer import Serializer


class Serializable(typing.Protocol):
    """Serialize this class into its xml representation and back."""

    @classmethod
    def serialize(cls, serializer: "Serializer") -> None:
        """
        Serialize the SiLA entity into the xml-based feature language definition.

        Args:
          serializer: The serializer instance used to write xml tokens.
        """
        ...

    @classmethod
    def deserialize(
        cls, deserializer: "Deserializer", context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, type[typing.Self]]:
        """
        Deserialize the xml-based feature language definition into SiLA entities.

        Args:
          deserializer: The deserializer instance used to read xml
            tokens.
          context: The deserialization context for the handler.

        Raises:
          ValueError: If an invalid or unexpected token is detected.
        """
        ...
