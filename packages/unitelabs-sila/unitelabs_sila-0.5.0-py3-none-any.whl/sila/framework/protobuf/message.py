import typing_extensions as typing

if typing.TYPE_CHECKING:
    from .reader import Reader
    from .writer import Writer


class Message(typing.Protocol):
    """Protocol for encoding and decoding Protocol Buffer messages."""

    @classmethod
    def decode(
        cls, reader: typing.Union["Reader", bytes, bytearray], length: typing.Optional[int] = None
    ) -> typing.Self:
        """
        Decode a message instance from a protobuf byte stream.

        Args:
          reader: The data source from which to decode the message.
          length: An optional length argument that indicates how much
            data to decode. If not provided, the entire message will be
            decoded.

        Returns:
          An instance of the decoded message.

        Raises:
          DecodeError: If there is an error while decoding the message.
        """
        ...

    def encode(self, writer: typing.Optional["Writer"] = None, number: typing.Optional[int] = None) -> bytes:
        """
        Encode the message instance into a protobuf byte stream.

        Args:
          writer: The data sink to which the encoded message will be
            written.
          number: An optional field number to associate with the message
            during encoding.

        Returns:
          The encoded message as bytes.

        Raises:
          EncodeError: If there is an error while encoding the message.
        """
        ...
