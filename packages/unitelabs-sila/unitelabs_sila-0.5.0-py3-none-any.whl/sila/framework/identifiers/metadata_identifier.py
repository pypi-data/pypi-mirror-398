import re

import typing_extensions as typing

from .feature_identifier import FeatureIdentifier, identifier


class MetadataIdentifier(FeatureIdentifier):
    """
    Uniquely identifies a metadata among all potentially existing metadatas.

    Attributes:
      metadata: Unique metadata identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/AuthorizationService/v1/Metadata/AccessToken"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{FeatureIdentifier._pattern}/Metadata/(?P<metadata>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int, metadata: str) -> typing.Self:
        """
        Create a new command parameter identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          metadata: Unique metadata identifier.

        Returns:
          The created command parameter identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}/Metadata/{metadata}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "metadata": metadata,
        }

        return identifier

    @property
    def metadata(self) -> str:
        """Unique metadata identifier."""

        return self._data["metadata"]
