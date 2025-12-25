import functools
import re

import typing_extensions as typing

from .feature_identifier import FeatureIdentifier, identifier


class CommandIdentifier(FeatureIdentifier):
    """
    Uniquely identifies a command among all potentially existing commands.

    Attributes:
      command: Unique command identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/SiLAService/v1/Command/GetFeatureDefinition"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{FeatureIdentifier._pattern}/Command/(?P<command>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int, command: str) -> typing.Self:
        """
        Create a new command identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          command: Unique command identifier.

        Returns:
          The created command identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}/Command/{command}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "command": command,
        }

        return identifier

    @property
    def command(self) -> str:
        """Unique command identifier."""

        return self._data["command"]

    @functools.cached_property
    def command_identifier(self) -> "CommandIdentifier":
        """The fully qualified command identifier."""

        return CommandIdentifier.create(self.originator, self.category, self.feature, self.version, self.command)
