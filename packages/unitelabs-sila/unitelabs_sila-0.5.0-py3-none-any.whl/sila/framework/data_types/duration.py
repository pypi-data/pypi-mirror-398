import dataclasses

import typing_extensions as typing

from sila import datetime

from ..protobuf import Message, Reader, WireType, Writer
from .convertable import Convertable

if typing.TYPE_CHECKING:
    from ..common import Context, Execution


@dataclasses.dataclass
class Duration(Message, Convertable):
    """
    A signed, fixed-length span of time at nanosecond resolution.

    Attributes:
      seconds: The seconds of the duration value. Defaults to zero.
      nanos: The nanos of the duration value. Defaults to zero.
    """

    seconds: int = 0
    nanos: int = 0

    @property
    def total_seconds(self) -> float:
        """Total seconds in the duration."""

        return self.seconds + self.nanos / 1_000_000_000

    @classmethod
    def from_total_seconds(cls, total_seconds: float) -> typing.Self:
        """Create a duration from the given seconds."""

        seconds = int(total_seconds)
        nanos = round((total_seconds - seconds) * 1_000_000_000)

        # Handle overflow or underflow of nanos
        if nanos >= 1_000_000_000:
            seconds += 1
            nanos -= 1_000_000_000
        elif nanos <= -1_000_000_000:
            seconds -= 1
            nanos += 1_000_000_000

        return cls(seconds=seconds, nanos=nanos)

    @classmethod
    def from_timedelta(cls, value: datetime.timedelta) -> typing.Self:
        """Create a SiLA `Duration` object from a `datetime.timedelta` object."""
        return cls(seconds=value.days * 86400 + value.seconds, nanos=value.microseconds * 1000)

    @typing.overload
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[datetime.timedelta] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self: ...

    @typing.overload
    @classmethod
    async def from_native(
        cls, context: "Context", /, *, seconds: int = 0, nanos: int = 0, execution: typing.Optional["Execution"]
    ) -> typing.Self: ...

    @typing.override
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[datetime.timedelta] = None,
        /,
        *,
        seconds: int = 0,
        nanos: int = 0,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        if value is None:
            return await cls(seconds=seconds, nanos=nanos).validate()

        return await cls.from_timedelta(value).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> datetime.timedelta:
        await self.validate()

        return datetime.timedelta(seconds=self.seconds, microseconds=int(self.nanos / 1000))

    @typing.override
    async def validate(self) -> typing.Self:
        if not isinstance(self.seconds, int):
            msg = f"Expected seconds of type 'int', received '{type(self.seconds).__name__}'."
            raise TypeError(msg)

        if not isinstance(self.nanos, int):
            msg = f"Expected nanos of type 'int', received '{type(self.nanos).__name__}'."
            raise TypeError(msg)

        if not (self.seconds >= 0):
            msg = f"Seconds must be a positive number, received '{self.seconds}'."
            raise ValueError(msg)

        if not (0 <= self.nanos < 1e9):
            msg = f"Nanos must be between 0 and 1e+9, received '{self.nanos}'."
            raise ValueError(msg)

        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.VARINT)
                message.seconds = reader.read_int64()
            elif field_number == 2:
                reader.expect_type(tag, WireType.VARINT)
                message.nanos = reader.read_int32()
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.seconds:
            writer.write_uint32(8).write_int64(self.seconds)
        if self.nanos:
            writer.write_uint32(16).write_int32(self.nanos)

        if number:
            writer.ldelim()

        return writer.finish()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented

        return self.seconds == other.seconds and self.nanos == other.nanos

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented

        return self.total_seconds < other.total_seconds

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented

        return self.total_seconds <= other.total_seconds

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented

        return self.total_seconds > other.total_seconds

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Duration):
            return NotImplemented

        return self.total_seconds >= other.total_seconds

    @typing.override
    def __hash__(self) -> int:
        return hash((self.seconds, self.nanos))
