import abc

import typing_extensions as typing

from ..fdl import Serializable

if typing.TYPE_CHECKING:
    from ..data_types import DataType

T = typing.TypeVar("T", bound="DataType", contravariant=True)


class Constraint(Serializable, typing.Generic[T], metaclass=abc.ABCMeta):
    """
    An abstract base class for defining constraints on values.

    Enforce specific rules on values by defining the validation logic
    in the the `validate` method.
    """

    @abc.abstractmethod
    async def validate(self, value: T) -> bool:
        """
        Validate the provided value against the constraint's rules.

        Args:
          value: The value to be validated.

        Returns:
          True if the value is valid according to the constraint.

        Raises:
          TypeError: If the provided value is not in the correct type.
          ValueError: If the provided value violates the constraints.
        """
