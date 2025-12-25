import re

import typing_extensions as typing

from .feature_identifier import FeatureIdentifier, identifier


class ErrorIdentifier(FeatureIdentifier):
    """
    Uniquely identifies a defined execution error among all potentially existing errors.

    Attributes:
      error: Unique defined execution error identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/SiLAService/v1/DefinedExecutionError/UnimplementedFeature"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{FeatureIdentifier._pattern}/DefinedExecutionError/(?P<error>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int, error: str) -> typing.Self:
        """
        Create a new defined execution error identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          error: Unique defined execution error identifier.

        Returns:
          The created defined execution error identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}/DefinedExecutionError/{error}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "error": error,
        }

        return identifier

    @property
    def error(self) -> str:
        """Unique defined execution error identifier."""

        return self._data["error"]
