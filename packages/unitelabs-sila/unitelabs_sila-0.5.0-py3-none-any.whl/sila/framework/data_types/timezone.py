import dataclasses
import re

import typing_extensions as typing

from sila import datetime

from ..protobuf import Message, Reader, WireType, Writer
from .convertable import Convertable

if typing.TYPE_CHECKING:
    from ..common import Context, Execution


TIMEZONE_FORMAT = re.compile("^(?P<sign>[+-])(?P<hours>\\d{2})(?::?(?P<minutes>\\d{2}))?$")


@dataclasses.dataclass
class Timezone(Message, Convertable):
    """
    A signed, fixed-length span of time representing an offset from UTC.

    Attributes:
      hours: The hours of the timezone value in range [-12-14].
        Defaults to zero.
      minutes: The minutes of the timezone value in range [0-59].
        Defaults to zero.
    """

    hours: int = 0
    minutes: int = 0

    @property
    def offset(self) -> int:
        """The offset in minutes of the timezone value."""

        return self.hours * 60 + self.minutes

    @classmethod
    def from_isoformat(cls, value: str) -> typing.Self:
        """
        Parse a `Timezone` from an ISO 8601 string.

        Args:
          value: The ISO 8601 string to parse.

        Returns:
          The parsed `Timezone`.

        Raises:
          ValueError: If the value is not a valid ISO 8601 timezone.
        """

        if value == "Z":
            return cls()

        match = TIMEZONE_FORMAT.match(value)
        if not match:
            msg = f"Expected ISO 8601 timezone with format '±hh:mm', received '{value}'."
            raise ValueError(msg) from None

        sign = -1 if match.group("sign") == "-" else 1
        offset = sign * (
            int(match.group("hours")) * 60 + (int(match.group("minutes")) if match.group("minutes") else 0)
        )
        hours, minutes = divmod(offset, 60)

        return cls(hours=hours, minutes=minutes)

    def to_isoformat(self) -> str:
        """
        Get the ISO 8601 string representation of the timezone.

        Returns:
          The ISO 8601 string representation of the timezone.
        """

        if self.hours == 0 and self.minutes == 0:
            return "Z"

        sign = "+" if self.offset >= 0 else "-"
        hours = abs(self.offset) // 60
        minutes = abs(self.offset) % 60

        return f"{sign}{hours:02d}:{minutes:02d}"

    @classmethod
    def from_timezone(cls, value: datetime.timezone) -> typing.Self:
        """Create a SiLA `Timezone` object from a `datetime.timezone` object."""
        if not isinstance(value, datetime.timezone):
            msg = f"Expected timezone of type 'datetime.timezone', received '{type(value).__name__}'."
            raise TypeError(msg) from None

        hour, minute = divmod(value.utcoffset(None).total_seconds() // 60, 60)
        offset = int(hour * 60 + minute)
        hours, minutes = divmod(offset, 60)
        return cls(hours=hours, minutes=minutes)

    @typing.override
    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[datetime.timezone] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        if value is None:
            return await cls().validate()

        return await cls.from_timezone(value).validate()

    @typing.override
    async def to_native(self, context: "Context", /) -> datetime.timezone:
        await self.validate()

        return datetime.timezone(offset=datetime.timedelta(minutes=self.offset))

    @typing.override
    async def validate(self) -> typing.Self:
        if not isinstance(self.hours, int):
            msg = f"Expected hours of type 'int', received '{type(self.hours).__name__}'."
            raise TypeError(msg)

        if not isinstance(self.minutes, int):
            msg = f"Expected minutes of type 'int', received '{type(self.minutes).__name__}'."
            raise TypeError(msg)

        if not (-14 <= self.hours <= 14):
            msg = f"Timezone hours must be between -14 and 14, received '{self.hours}'."
            raise ValueError(msg)

        if not (0 <= self.minutes <= 59):
            msg = f"Timezone minutes must be between 0 and 59, received '{self.minutes}'."
            raise ValueError(msg)

        if self.offset < -840 or self.offset > 840:
            msg = f"Timezone must be between -14:00 and 14:00, received '{self.to_isoformat()}'."
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
                message.hours = reader.read_int32()
            elif field_number == 2:
                reader.expect_type(tag, WireType.VARINT)
                message.minutes = reader.read_uint32()
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.hours:
            writer.write_uint32(8).write_int32(self.hours)
        if self.minutes:
            writer.write_uint32(16).write_uint32(self.minutes)

        if number:
            writer.ldelim()

        return writer.finish()

    @typing.override
    def __str__(self) -> str:
        return self.to_isoformat()

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented

        return self.hours == other.hours and self.minutes == other.minutes

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented

        return self.offset < other.offset

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented

        return self.offset <= other.offset

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented

        return self.offset > other.offset

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Timezone):
            return NotImplemented

        return self.offset >= other.offset

    @typing.override
    def __hash__(self) -> int:
        return hash((self.hours, self.minutes))
