import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.date import Date
from ..data_types.integer import Integer
from ..data_types.real import Real
from ..data_types.string import String
from ..data_types.time import Time
from ..data_types.timestamp import Timestamp
from ..fdl import Characters, Deserializer, EndElement, Serializer, StartElement
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List

T = typing.TypeVar("T", String, Integer, Real, Date, Time, Timestamp)


@dataclasses.dataclass
class Set(Constraint[T]):
    """
    A constraint that enforces that a value is part of a defined set of values.

    Raises:
      ValueError: If the list of allowed values is empty.
    """

    values: collections.abc.Sequence[T]
    """A sequence of allowed values."""

    def __post_init__(self):
        if not self.values:
            msg = "The list of allowed values must not be empty."
            raise ValueError(msg)

        self.__type = type(self.values[0])

        if any(type(value) is not self.__type for value in self.values):
            msg = "The list of allowed values must all have the same type."
            raise TypeError(msg)

    @typing.override
    async def validate(self, value: T) -> bool:
        if not isinstance(value, self.__type):
            msg = f"Expected value of type '{self.__type.__name__}', received '{type(value).__name__}'."
            raise TypeError(msg)

        if value not in self.values:
            msg = f"Value '{value}' is not in the set of allowed values."
            raise ValueError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.start_element("Set")
        for value in self.values:
            serializer.write_str("Value", str(value))

        serializer.end_element("Set")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, (String, Integer, Real, Date, Time, Timestamp)):
            msg = (
                f"Expected constraint's data type to be 'String', 'Integer', 'Real', 'Date', 'Time' or 'Timestamp', "
                f"received '{data_type.__name__}'."
            )
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="Set")

        values: list[T] = []
        while True:
            token = yield

            if isinstance(token, StartElement):
                if token.name == "Value":
                    if issubclass(data_type, String):
                        value = yield from deserializer.read_str()
                    elif issubclass(data_type, Integer):
                        value = yield from deserializer.read_integer()
                    elif issubclass(data_type, Real):
                        value = yield from deserializer.read_float()
                    elif issubclass(data_type, Date):
                        value = yield from deserializer.read_date()
                    elif issubclass(data_type, Time):
                        value = yield from deserializer.read_time()
                    elif issubclass(data_type, Timestamp):
                        value = yield from deserializer.read_timestamp()

                    values.append(typing.cast(T, value))
                else:
                    msg = f"Expected start element with name 'Value', received start element with name '{token.name}'."
                    raise ValueError(msg)

            elif isinstance(token, EndElement):
                if token.name == "Value":
                    continue
                else:
                    break  # pragma: no cover

            elif isinstance(token, Characters):
                msg = f"Expected start element with name 'Value', received characters '{token.value}'."
                raise ValueError(msg)

        if not values:
            msg = "Expected at least one 'Value' element inside the 'Set' element."
            raise ValueError(msg)

        return cls(values)
