import dataclasses

from ..validators import check_display_name, check_identifier
from .any import Any
from .data_type import DataType


@dataclasses.dataclass
class Element:
    """
    An element represents an entry in the SiLA structure data type.

    Attributes:
      identifier: Uniquely identifies the structure element within
        the scope of its structure data type. Uniqueness is checked
        without taking lower and upper case into account. Should be
        in pascal case.
      display_name: Human readable name of the structure element.
        Should be the identifier with spaces between separate words.
      description: Describes the use and purpose of the structure
        element.
      data_type: The SiLA data type of the structure element.
    """

    identifier: str
    display_name: str
    description: str = ""
    data_type: type[DataType] = Any

    def __post_init__(self) -> None:
        check_identifier(self.identifier)
        check_display_name(self.display_name)
