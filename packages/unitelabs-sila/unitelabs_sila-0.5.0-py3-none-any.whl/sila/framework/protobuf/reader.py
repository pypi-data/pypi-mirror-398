import contextlib
import struct

import typing_extensions as typing

from .decode_error import DecodeError
from .wire_type import WireType


class Reader:
    """
    A data source from which to decode a Protocol Buffer message.

    Args:
      buffer: A buffer containing the data to be read.
    """

    def __init__(self, buffer: typing.Union[bytes, bytearray]) -> None:
        self.buf = buffer if isinstance(buffer, bytearray) else bytearray(buffer)
        self.len = len(buffer)
        self.cur = 0

    @property
    def buffer(self) -> bytearray:
        """The internal buffer that holds the provided byte data."""

        return self.buf

    @property
    def length(self) -> int:
        """The total length of the byte buffer."""

        return self.len

    @property
    def cursor(self) -> int:
        """The current read position within the buffer."""

        return self.cur

    def read_varint(self) -> int:
        """
        Decode a variable-length integer encoded in the buffer.

        Returns:
          The decoded variable-length integer.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        value = 0
        shift = 0

        while True:
            # Check if we've reached the end of the buffer
            if self.cur >= self.len:
                msg = "Buffer does not contain enough bytes to decode a variable-length integer."
                raise DecodeError(msg, offset=self.cur)

            byte = self.buf[self.cur]
            self.cur += 1
            value |= (byte & 0x7F) << shift

            # If the MSB is 0, this is the last byte of the varint
            if byte & 0x80 == 0:
                return value

            shift += 7

            # Check for overflow; varints are limited to 64 bits
            if shift >= 64:
                msg = "Variable-length integer is too large."
                raise DecodeError(msg, offset=self.cur)

    def read_uint32(self) -> int:
        """
        Read a variable-length unsigned 32-bit integer from the current buffer position.

        Returns:
          The decoded unsigned 32-bit integer.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        varint = self.read_varint()

        if not (0 <= varint <= (1 << 32) - 1):
            msg = "Variable-length integer overflows its maximum size of 32 bit."
            raise DecodeError(msg, self.cur)

        return varint

    def read_int32(self) -> int:
        """
        Read a variable-length signed 32-bit integer from the current buffer position.

        Returns:
          The decoded signed 32-bit integer.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        value = self.read_varint()

        return value if value < (1 << 63) else value - (1 << 64)

    def read_uint64(self) -> int:
        """
        Read a variable-length unsigned 64-bit integer from the current buffer position.

        Returns:
          The decoded unsigned 64-bit integer.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        return self.read_varint()

    def read_int64(self) -> int:
        """
        Read a variable-length signed 64-bit integer from the current buffer position.

        Returns:
          The decoded signed 64-bit integer.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        value = self.read_varint()

        return value if value < (1 << 63) else value - (1 << 64)

    def read_double(self) -> float:
        """
        Read a 64-bit double-precision floating-point number from the current buffer position.

        Returns:
          The decoded double-precision floating-point number.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        parser = struct.Struct("<d")
        try:
            value = float(parser.unpack_from(self.buf, self.cur)[0])
            self.cur += 8

            return value
        except struct.error:
            msg = "Buffer does not contain enough bytes to read a double-precision floating-point number."
            raise DecodeError(msg, offset=self.cur) from None

    def read_bool(self) -> bool:
        """
        Read a boolean value from the current buffer position.

        Returns:
          The decoded boolean value.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        return self.read_uint32() == 1

    def read_bytes(self) -> bytes:
        """
        Read a length-prefixed byte sequence from the current buffer position.

        Returns:
          The extracted byte sequence.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        # Read the length of the byte sequence
        length = self.read_uint32()
        end = self.cur + length

        if end > self.len:
            msg = (
                f"Attempted to read {length} bytes at position {self.cur}, but the buffer only has "
                f"{self.len - self.cur} remaining bytes. Cannot read past the end of the buffer."
            )
            raise DecodeError(msg, offset=self.cur)

        # Extract the byte sequence
        result = self.buf[self.cur : end]
        self.cur = end

        return bytes(result)

    def read_string(self) -> str:
        """
        Read a length-prefixed string sequence from the current buffer position.

        Returns:
          The extracted string sequence.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        return self.read_bytes().decode("utf-8")

    def skip(self, length: typing.Optional[int] = None) -> "Reader":
        """
        Advance the reader's position in the buffer by a specified number of bytes.

        Args:
          length: The number of bytes to skip. If omitted, skips a varint.

        Returns:
          The current instance, allowing method chaining.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        if length is not None:
            if self.cur + length > self.len:
                msg = (
                    f"Attempted to skip {length} bytes from position {self.cur}, but the buffer only has "
                    f"{self.len - self.cur} remaining bytes. Cannot read past the end of the buffer."
                )
                raise DecodeError(msg, offset=self.cur)

            self.cur += length
        else:
            self.read_uint32()

        return self

    def skip_type(self, wire_type: int) -> "Reader":
        """
        Skip over a protobuf field based on its wire type.

        Args:
          wire_type: The protobuf wire type to skip.

        Returns:
          The current instance, allowing method chaining.

        Raises:
          DecodeError: If the buffer does not contain enough bytes or is
            too large.
        """

        cursor = self.cur
        if wire_type == WireType.VARINT:
            self.skip()
        elif wire_type == WireType.I64:
            self.skip(8)
        elif wire_type == WireType.LEN:
            self.skip(self.read_uint32())
        elif wire_type == WireType.I32:
            self.skip(4)
        else:
            value = str(wire_type)
            with contextlib.suppress(ValueError):
                value = WireType(wire_type).name

            msg = f"Invalid wire type '{value}' at offset '{cursor}'."
            raise DecodeError(msg, cursor)

        return self

    def expect_type(self, tag: int, expected: WireType) -> None:
        """
        Expect the given wire type.

        Args:
          tag: The decoded tag containing the wire type.
          expected: The expected wire type.

        Raises:
          DecodeError: If the decoded wire type does not match the
            expected one.
        """

        wire_type = WireType(tag & 7)
        if wire_type != expected:
            msg = f"Expected wire type '{expected.name}', received '{wire_type.name}'."

            raise DecodeError(msg, self.cur)
