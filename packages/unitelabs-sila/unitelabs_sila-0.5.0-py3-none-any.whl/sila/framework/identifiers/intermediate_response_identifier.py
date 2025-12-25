import re

import typing_extensions as typing

from .command_identifier import CommandIdentifier
from .feature_identifier import identifier


class IntermediateResponseIdentifier(CommandIdentifier):
    """
    Uniquely identifies an intermediate response of a command.

    Attributes:
      intermediate_response: Unique intermediate response identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/test/ObservableCommandTest/v1/Command/Count/IntermediateResponse/CurrentIteration"
      ... )
    """

    _pattern: typing.ClassVar[str] = (
        f"{CommandIdentifier._pattern}/IntermediateResponse/(?P<intermediate_response>{identifier})"
    )
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(
        cls, originator: str, category: str, feature: str, version: int, command: str, intermediate_response: str
    ) -> typing.Self:
        """
        Create a new intermediate command response identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          command: Unique command identifier.
          intermediate_response: Unique intermediate response identifier.

        Returns:
          The created intermediate command response identifier.
        """

        identifier = super().__new__(
            cls,
            f"{originator}/{category}/{feature}/v{version}/Command/{command}/IntermediateResponse/{intermediate_response}",
        )
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "command": command,
            "intermediate_response": intermediate_response,
        }

        return identifier

    @property
    def intermediate_response(self) -> str:
        """Unique intermediate response identifier."""

        return self._data["intermediate_response"]
