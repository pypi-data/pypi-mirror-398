import io
import struct

from .encode_error import EncodeError


class Writer:
    """A data sink to which an encoded Protocol Buffer message can be written."""

    def __init__(self):
        self.buf = [io.BytesIO()]
        self.len = 0

    @property
    def buffer(self) -> io.BytesIO:
        """The internal buffer that holds the provided byte data."""

        return self.buf[-1]

    @property
    def length(self) -> int:
        """The total length of the byte buffer."""

        return self.len

    def write_varint(self, value: int) -> "Writer":
        """
        Encode a variable-length integer (varint) in Protocol Buffer format and write it to the buffer.

        Args:
          value: The integer value to encode as a varint. Must be
            non-negative.

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the input value is negative, as varint encoding
            does not support negative integers.
        """

        if value < 0:
            msg = "Varint encoding does not support negative values."
            raise EncodeError(msg)

        while value > 0x7F:
            # Write 7 bits and set MSB to 1.
            self.buffer.write(bytes((value & 0x7F | 0x80,)))
            # Shift value right by 7 bits.
            value >>= 7
            self.len += 1

        # Write the final 7 bits (MSB = 0).
        self.buffer.write(bytes((value,)))
        self.len += 1

        return self

    def write_uint32(self, value: int) -> "Writer":
        """
        Encode an unsigned 32-bit integer as a varint and write it to the buffer.

        Args:
          value: The unsigned 32-bit integer to encode and write. Must be
          in the range [0, 2^32 - 1].

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the value is not within the range of an unsigned
            32-bit integer.
        """

        if not (0 <= value < (1 << 32)):
            msg = "Value must be a 32-bit unsigned integer (0 <= value < 2^32)."
            raise EncodeError(msg)

        return self.write_varint(value)

    def write_int32(self, value: int) -> "Writer":
        """
        Encode a signed 32-bit integer as a varint and write it to the buffer.

        Args:
          value: The signed 32-bit integer to encode and write. Must be
            in the range [-2^31, 2^31 - 1].

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the value is not within the range of a signed
            32-bit integer.
        """

        if not (-(1 << 31) <= value < (1 << 31)):
            msg = "Value must be a 32-bit signed integer (-2^31 <= value < 2^31)."
            raise EncodeError(msg)

        # Map negative values to the unsigned space using two's complement
        if value < 0:
            value += 1 << 64

        return self.write_varint(value)

    def write_uint64(self, value: int) -> "Writer":
        """
        Encode an unsigned 64-bit integer as a varint and write it to the buffer.

        Args:
          value: The unsigned 64-bit integer to encode and write. Must be
            in the range [0, 2^64 - 1].

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the value is not within the range of an unsigned
            64-bit integer.
        """

        if not (0 <= value < (1 << 64)):
            msg = "Value must be a 64-bit unsigned integer (0 <= value < 2^64)."
            raise EncodeError(msg)

        return self.write_varint(value)

    def write_int64(self, value: int) -> "Writer":
        """
        Encode a signed 64-bit integer as a varint and write it to the buffer.

        Args:
          value: The signed 64-bit integer to encode and write. Must be
            in the range [-2^63, 2^63 - 1].

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the value is not within the range of a signed
            64-bit integer.
        """

        if not (-(1 << 63) <= value < (1 << 63)):
            msg = "Value must be a 64-bit signed integer (-2^63 <= value < 2^63)."
            raise EncodeError(msg)

        # Map negative values to the unsigned space using two's complement
        if value < 0:
            value += 1 << 64

        return self.write_varint(value)

    def write_double(self, value: float) -> "Writer":
        """
        Encode a 64-bit double-precision floating-point number (IEEE 754) and write it to the buffer.

        Args:
          value: The double-precision floating-point number to encode and
            write.

        Returns:
          The Writer instance, allowing for method chaining.

        Raises:
          EncodeError: If the value is not within the range of a 64-bit
            floating-point number.
        """

        try:
            # Encode the float as a fixed 8-byte little-endian representation
            buffer = struct.Struct("<d").pack(value)
        except struct.error:
            msg = "Value must be a 64-bit double-precision floating-point number."
            raise EncodeError(msg) from None

        self.buffer.write(buffer)
        self.len += 8

        return self

    def write_bool(self, value: bool) -> "Writer":
        """
        Encode a boolean value as a single byte and write it to the buffer.

        Args:
          value: The boolean value to encode and write.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        self.buffer.write(b"\x01" if value else b"\x00")
        self.len += 1

        return self

    def write_bytes(self, value: bytes) -> "Writer":
        """
        Encode a byte sequence with a length prefix and write it to the buffer.

        Args:
          value: The byte sequence to encode and write.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        length = len(value)

        # Write the length prefix as a varint
        self.write_varint(length)

        # Write the byte sequence (if non-empty)
        if length > 0:
            self.buffer.write(value)
            self.len += length

        return self

    def write_string(self, value: str) -> "Writer":
        """
        Encode a UTF-8 string with a length prefix and writes it to the buffer.

        Args:
          value: The string to encode and write.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        return self.write_bytes(value.encode("utf-8"))

    def write(self, value: bytes) -> "Writer":
        """
        Write raw bytes directly to the buffer.

        Args:
          value: The byte sequence to write.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        self.buffer.write(value)
        self.len += len(value)

        return self

    def fork(self) -> "Writer":
        """
        Create a new fork within the buffer.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        self.buf.append(io.BytesIO())

        return self

    def ldelim(self) -> "Writer":
        """
        Prefix the current fork with its length and write it into the buffer.

        Returns:
          The Writer instance, allowing for method chaining.
        """

        fork = self.buf.pop()
        value = fork.getvalue()
        length = len(value)

        self.write_varint(length)
        self.buffer.write(value)

        fork.close()

        return self

    def finish(self) -> bytes:
        """
        Finalize the writer and retrieves the serialized data.

        Returns:
          The serialized data from the writer's buffer.
        """

        return self.buffer.getvalue()
