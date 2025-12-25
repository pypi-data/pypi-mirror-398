import collections.abc
import dataclasses

import typing_extensions as typing

from ..data_types.any import Any
from ..data_types.data_type import DataType
from ..fdl import Deserializer, EndElement, Serializer, StartElement
from .constraint import Constraint


@dataclasses.dataclass
class AllowedTypes(Constraint[Any]):
    """A constraint that specifies a set of allowed data types for an `Any` value."""

    values: collections.abc.Sequence[type["DataType"]]
    """
    A sequence of allowed data types that the input value must match.
    """

    @typing.override
    async def validate(self, value: Any) -> bool:
        is_valid = any(item.equals(type(value.value)) for item in self.values)

        if not is_valid:
            msg = (
                "Expected data type to be one of "
                + ", ".join(item.__name__ for item in self.values)
                + f", received {type(value.value).__name__}."
            )
            raise ValueError(msg)

        return True

    @typing.override
    def serialize(self, serializer: Serializer) -> None:
        serializer.start_element("AllowedTypes")
        for value in self.values:
            value.serialize(serializer)
        serializer.end_element("AllowedTypes")

    @typing.override
    @classmethod
    def deserialize(
        cls, deserializer: Deserializer, context: typing.Optional[dict] = None
    ) -> collections.abc.Generator[None, typing.Any, typing.Self]:
        data_type: typing.Union[None, type["Any"]] = (context or {}).get("data_type", None)

        if data_type is None:
            msg = "Missing 'data_type' in context."
            raise ValueError(msg)

        if not issubclass(data_type, (Any)):
            msg = f"Expected constraint's data type to be 'Any', received '{data_type.__name__}'."
            raise ValueError(msg)

        yield from deserializer.read_start_element(name="AllowedTypes")

        data_types: list[type[DataType]] = []
        while True:
            token = yield from deserializer.peek()

            if token == StartElement("DataType"):
                inner_data_type = yield from deserializer.read(DataType.deserialize)
                data_types.append(inner_data_type)

            elif token == EndElement("AllowedTypes"):
                break

        yield from deserializer.read_end_element(name="AllowedTypes")

        return cls(data_types)
