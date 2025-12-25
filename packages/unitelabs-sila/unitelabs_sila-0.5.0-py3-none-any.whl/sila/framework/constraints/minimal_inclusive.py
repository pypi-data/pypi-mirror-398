import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.date import Date
from ..data_types.integer import Integer
from ..data_types.real import Real
from ..data_types.time import Time
from ..data_types.timestamp import Timestamp
from ..fdl import Deserializer, Serializer
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List

T = typing.TypeVar("T", Integer, Real, Date, Time, Timestamp)


@dataclasses.dataclass
class MinimalInclusive(Constraint[T]):
    """A constraint that enforces a lower inclusive bound on a value."""

    value: T
    """
    The lower inclusive limit for the value.
    """

    @typing.override
    async def validate(self, value: T) -> bool:
        if not isinstance(value, type(self.value)):
            msg = f"Expected value of type '{type(self.value).__name__}', received '{type(value).__name__}'."
            raise TypeError(msg)

        if value < self.value:
            msg = f"Value '{value}' must be greater than or equal to the minimal inclusive limit of '{self.value}'."
            raise ValueError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.write_str("MinimalInclusive", str(self.value))

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, (Integer, Real, Date, Time, Timestamp)):
            msg = (
                f"Expected constraint's data type to be 'Integer', 'Real', 'Date', 'Time' or 'Timestamp', "
                f"received '{data_type.__name__}'."
            )
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="MinimalInclusive")
        if issubclass(data_type, Integer):
            value = yield from deserializer.read_integer()
        elif issubclass(data_type, Real):
            value = yield from deserializer.read_float()
        elif issubclass(data_type, Date):
            value = yield from deserializer.read_date()
        elif issubclass(data_type, Time):
            value = yield from deserializer.read_time()
        elif issubclass(data_type, Timestamp):
            value = yield from deserializer.read_timestamp()
        yield from deserializer.read_end_element(name="MinimalInclusive")

        return cls(typing.cast(T, value))
