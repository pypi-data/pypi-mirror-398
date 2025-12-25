import dataclasses
import inspect
import re

import typing_extensions as typing

from sila import datetime

from ..protobuf import DecodeError, Reader, WireType, Writer
from .data_type import BasicType
from .timezone import Timezone

if typing.TYPE_CHECKING:
    from ..common import Context, Execution

TIME_FORMAT = re.compile(
    "^(?P<hour>\\d{2}):(?P<minute>\\d{2}):(?P<second>\\d{2})(?:\\.(?P<millisecond>\\d{3}))?(?P<timezone>.*)$",
)


@dataclasses.dataclass
class Time(BasicType[datetime.time]):
    """
    Represents an ISO 8601 time, with an additional timezone (as an offset from UTC).

    Attributes:
      hour: The hour of the time value in range [0-23]. Defaults to
        zero.
      minute: The minute of the time value in range [0-59]. Defaults
        to zero.
      second: The second of the time value in range [0-59]. Defaults
        to zero.
      millisecond: The millisecond of the time value in range
        [0-999]. Defaults to zero.
      timezone: The timezone of the time value. Defaults to utc.
    """

    hour: int = 0
    minute: int = 0
    second: int = 0
    millisecond: int = 0
    timezone: Timezone = dataclasses.field(default_factory=Timezone)

    @property
    def timestamp(self, /) -> float:
        """Return the POSIX timestamp of the time."""

        return datetime.datetime(
            1970,
            1,
            1,
            self.hour,
            self.minute,
            self.second,
            self.millisecond * 1000,
            tzinfo=datetime.timezone(datetime.timedelta(minutes=self.timezone.offset)),
        ).timestamp()

    @classmethod
    def from_isoformat(cls, value: str) -> typing.Self:
        """
        Parse a `Time` from an ISO 8601 string.

        Args:
          value: The ISO 8601 string to parse.

        Returns:
          The parsed `Time`.

        Raises:
          ValueError: If the value is not a valid ISO 8601 time.
        """

        match = TIME_FORMAT.match(value)
        if not match:
            msg = f"Expected ISO 8601 time with format 'hh:mm:ss.sss±hh:mm', received '{value}'."
            raise ValueError(msg) from None

        return cls(
            hour=int(match.group("hour")),
            minute=int(match.group("minute")),
            second=int(match.group("second")),
            millisecond=int(match.group("millisecond")) if match.group("millisecond") else 0,
            timezone=Timezone.from_isoformat(match.group("timezone") or "Z"),
        )

    def to_isoformat(self) -> str:
        """
        Get the ISO 8601 string representation of the time.

        Returns:
          The ISO 8601 string representation of the time.
        """

        return (
            f"{self.hour:02d}:{self.minute:02d}:{self.second:02d}.{self.millisecond:03d}{self.timezone.to_isoformat()}"
        )

    @classmethod
    def from_time(cls, value: datetime.time) -> typing.Self:
        """Create a SiLA `Time` object from a `datetime.time` object."""
        if not isinstance(value, datetime.time):
            msg = f"Expected time of type 'datetime.time', received '{type(value).__name__}'."
            raise TypeError(msg) from None

        return cls(
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            millisecond=int(value.microsecond / 1000),
            timezone=Timezone.from_timezone(
                datetime.timezone(offset)
                if (tzinfo := getattr(value, "tzinfo", None))
                and isinstance(tzinfo, datetime.tzinfo)
                and (offset := tzinfo.utcoffset(None))
                else datetime.timezone.utc,
            ),
        )

    @typing.override
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[datetime.time] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        if value is None:
            return await cls().validate()

        return await cls.from_time(value).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> datetime.time:
        await self.validate()

        return datetime.time(
            hour=int(self.hour),
            minute=int(self.minute),
            second=int(self.second),
            microsecond=int(self.millisecond) * 1000,
            tzinfo=await self.timezone.to_native(context) if self.timezone else None,
        )

    @typing.override
    async def validate(self) -> typing.Self:
        if not isinstance(self.hour, int):
            msg = f"Expected hour of type 'int', received '{type(self.hour).__name__}'."
            raise TypeError(msg)

        if not isinstance(self.minute, int):
            msg = f"Expected minute of type 'int', received '{type(self.minute).__name__}'."
            raise TypeError(msg)

        if not isinstance(self.second, int):
            msg = f"Expected second of type 'int', received '{type(self.second).__name__}'."
            raise TypeError(msg)

        if not isinstance(self.millisecond, int):
            msg = f"Expected millisecond of type 'int', received '{type(self.millisecond).__name__}'."
            raise TypeError(msg)

        if not (0 <= self.hour <= 23):
            msg = f"Hour must be between 0 and 23, received '{self.hour}'."
            raise ValueError(msg)

        if not (0 <= self.minute <= 59):
            msg = f"Minute must be between 0 and 59, received '{self.minute}'."
            raise ValueError(msg)

        if not (0 <= self.second <= 59):
            msg = f"Second must be between 0 and 59, received '{self.second}'."
            raise ValueError(msg)

        if not (0 <= self.millisecond <= 999):
            msg = f"Millisecond must be between 0 and 999, received '{self.millisecond}'."
            raise ValueError(msg)

        return self

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls()
        timezone = None
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.VARINT)
                message.second = reader.read_int32()
            elif field_number == 2:
                reader.expect_type(tag, WireType.VARINT)
                message.minute = reader.read_uint32()
            elif field_number == 3:
                reader.expect_type(tag, WireType.VARINT)
                message.hour = reader.read_uint32()
            elif field_number == 4:
                reader.expect_type(tag, WireType.LEN)
                timezone = Timezone.decode(reader, reader.read_uint32())
            elif field_number == 5:
                reader.expect_type(tag, WireType.VARINT)
                message.millisecond = reader.read_uint32()
            else:
                reader.skip_type(tag & 7)

        if timezone is None:
            msg = "Missing field 'timezone' in message 'Time'."
            raise DecodeError(msg, offset=reader.cursor)

        message.timezone = timezone

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.second:
            writer.write_uint32(8).write_uint32(self.second)
        if self.minute:
            writer.write_uint32(16).write_uint32(self.minute)
        if self.hour:
            writer.write_uint32(24).write_uint32(self.hour)
        self.timezone.encode(writer, 4)
        if self.millisecond:
            writer.write_uint32(40).write_uint32(self.millisecond)

        if number:
            writer.ldelim()

        return writer.finish()

    @typing.override
    @classmethod
    def equals(cls, other: object) -> bool:
        return inspect.isclass(other) and issubclass(other, Time)

    @typing.override
    def __str__(self) -> str:
        return self.to_isoformat()

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented

        return (
            self.hour == other.hour
            and self.minute == other.minute
            and self.second == other.second
            and self.millisecond == other.millisecond
            and self.timezone == other.timezone
        )

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented

        return self.timestamp < other.timestamp

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented

        return self.timestamp <= other.timestamp

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented

        return self.timestamp > other.timestamp

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented

        return self.timestamp >= other.timestamp

    @typing.override
    def __hash__(self) -> int:
        return hash((self.hour, self.minute, self.second, self.millisecond, self.timezone))
