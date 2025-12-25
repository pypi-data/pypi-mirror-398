import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.binary import Binary
from ..data_types.string import String
from ..fdl import Deserializer, Serializer
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType, List

T = typing.TypeVar("T", String, Binary)


@dataclasses.dataclass
class MinimalLength(Constraint[T]):
    """
    A constraint that enforces a minimal length for a `String` or `Binary` value.

    Raises:
      ValueError: If `value` is negative or exceeds 2⁶³.
    """

    value: int
    """
    The minimal allowed length for the value. Must be a non-negative
    integer and less than 2⁶³.
    """

    def __post_init__(self):
        if self.value < 0:
            msg = f"Minimal length must be a non-negative integer, received '{self.value}'."
            raise ValueError(msg)

        if self.value >= 2**63:
            msg = f"Minimal length must be less than 2⁶³, received '{self.value}'."
            raise ValueError(msg)

    @typing.override
    async def validate(self, value: T) -> bool:
        if not isinstance(value, (String, Binary)):
            msg = f"Expected value of type 'String' or 'Binary', received '{type(value).__name__}'."
            raise TypeError(msg)

        if len(value.value) < self.value:
            msg = f"Expected value with minimal length '{self.value}', received '{len(value.value)}'."
            raise ValueError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.write_str("MinimalLength", str(self.value))

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, (String, Binary)):
            msg = f"Expected constraint's data type to be 'String' or 'Binary', received '{data_type.__name__}'."
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="MinimalLength")
        value = yield from deserializer.read_integer()
        yield from deserializer.read_end_element(name="MinimalLength")

        return cls(value.value)
