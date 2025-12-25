import re

import typing_extensions as typing

from .command_identifier import CommandIdentifier
from .feature_identifier import identifier


class ParameterIdentifier(CommandIdentifier):
    """
    Uniquely identifies a parameter of a command.

    Attributes:
      parameter: Unique parameter identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/SiLAService/v1/Command/GetFeatureDefinition/Parameter/FeatureIdentifier"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{CommandIdentifier._pattern}/Parameter/(?P<parameter>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(
        cls, originator: str, category: str, feature: str, version: int, command: str, parameter: str
    ) -> typing.Self:
        """
        Create a new command parameter identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          command: Unique command identifier.
          parameter: Unique parameter identifier.

        Returns:
          The created command parameter identifier.
        """

        identifier = super().__new__(
            cls, f"{originator}/{category}/{feature}/v{version}/Command/{command}/Parameter/{parameter}"
        )
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "command": command,
            "parameter": parameter,
        }

        return identifier

    @property
    def parameter(self) -> str:
        """Unique parameter identifier."""

        return self._data["parameter"]
