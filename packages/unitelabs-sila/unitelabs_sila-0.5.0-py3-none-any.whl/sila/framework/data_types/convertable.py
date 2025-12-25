import collections.abc
import datetime

import typing_extensions as typing

from ..common import Execution

if typing.TYPE_CHECKING:
    from ..common import Context, Execution
    from .data_type import DataType


class IAny(typing.Protocol):
    """Interface for any data type."""

    value: "DataType"


Native = typing.Union[
    str,
    int,
    float,
    bool,
    bytes,
    datetime.date,
    datetime.time,
    datetime.datetime,
    collections.abc.Sequence["Native"],
    collections.abc.Mapping[str, "Native"],
    IAny,
]

T = typing.TypeVar("T", bound=Native)


class Convertable(typing.Protocol[T]):
    """Convert a native Python value to this class and back."""

    @classmethod
    async def from_native(
        cls,
        context: "Context",
        value: typing.Optional[T] = None,
        /,
        *,
        execution: typing.Optional["Execution"] = None,
    ) -> typing.Self:
        """
        Convert a native Python value to its corresponding SiLA data type.

        Args:
          context: The context in which the conversion is performed.
          value: The native value to convert. If not provided, an
            instance with a default value is created.
          execution: The context of the current command execution.

        Returns:
          An instance of the corresponding SiLA data type.

        Raises:
          ConversionError: If the provided native value cannot be
            converted to the SiLA data type.
        """
        ...

    async def to_native(self, context: "Context", /) -> T:
        """
        Convert the SiLA data type to a native Python value.

        Args:
          context: The context in which the conversion is performed.

        Returns:
          The native Python value corresponding to the SiLA data type.

        Raises:
          ConversionError: If the SiLA data type cannot be converted to a
            native Python value.
        """
        ...

    async def validate(self) -> typing.Self:
        """
        Test constraints and restrictions of the data type value.

        Returns:
          The data type instance, allowing for method chaining.

        Raises:
          TypeError: If the value has an incorrect type.
          ValueError: If the value does not comply with the given
            constraints and restrictions.
        """
        ...
