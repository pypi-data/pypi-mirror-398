import re

import typing_extensions as typing

from .command_identifier import CommandIdentifier
from .feature_identifier import identifier


class ResponseIdentifier(CommandIdentifier):
    """
    Uniquely identifies a response of a command.

    Attributes:
      response: Unique response identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/SiLAService/v1/Command/GetFeatureDefinition/Response/FeatureDefinition"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{CommandIdentifier._pattern}/Response/(?P<response>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(
        cls, originator: str, category: str, feature: str, version: int, command: str, response: str
    ) -> typing.Self:
        """
        Create a new command response identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          command: Unique command identifier.
          response: Unique response identifier.

        Returns:
          The created command response identifier.
        """

        identifier = super().__new__(
            cls, f"{originator}/{category}/{feature}/v{version}/Command/{command}/Response/{response}"
        )
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "command": command,
            "response": response,
        }

        return identifier

    @property
    def response(self) -> str:
        """Unique response identifier."""

        return self._data["response"]
