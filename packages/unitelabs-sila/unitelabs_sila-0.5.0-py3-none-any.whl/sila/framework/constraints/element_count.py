import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.list import List
from ..fdl import Deserializer, Serializer
from .constraint import Constraint

if typing.TYPE_CHECKING:
    from ..data_types import BasicType


@dataclasses.dataclass
class ElementCount(Constraint[List]):
    """
    A constraint that enforces an exact element count for a `List` value.

    Raises:
      ValueError: If `value` is negative or exceeds 2⁶³.
    """

    value: int
    """
    The exact number of elements allowed in the `List`. Must be a
    non-negative integer and less than 2⁶³.
    """

    def __post_init__(self):
        if self.value < 0:
            msg = f"Element count must be a non-negative integer, received '{self.value}'."
            raise ValueError(msg)

        if self.value >= 2**63:
            msg = f"Element count must be less than 2⁶³, received '{self.value}'."
            raise ValueError(msg)

    @typing.override
    async def validate(self, value: List) -> bool:
        if not isinstance(value, List):
            msg = f"Expected value of type 'List', received '{type(value).__name__}'."
            raise TypeError(msg)

        if len(value.value) != self.value:
            msg = f"Expected list with element count '{self.value}', received '{len(value.value)}'."
            raise ValueError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.write_str("ElementCount", str(self.value))

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["BasicType"], type["List"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, List):
            msg = f"Expected constraint's data type to be 'List', received '{data_type.__name__}'."
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="ElementCount")
        value = yield from deserializer.read_integer()
        yield from deserializer.read_end_element(name="ElementCount")

        return cls(value.value)
