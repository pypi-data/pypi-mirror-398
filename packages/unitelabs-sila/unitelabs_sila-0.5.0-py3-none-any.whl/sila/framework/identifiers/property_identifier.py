import re

import typing_extensions as typing

from .feature_identifier import FeatureIdentifier, identifier


class PropertyIdentifier(FeatureIdentifier):
    """
    Uniquely identifies a property among all potentially existing properties.

    Attributes:
      property: Unique property identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/SiLAService/v1/Property/ServerUUID"
      ... )
    """

    _pattern: typing.ClassVar[str] = rf"{FeatureIdentifier._pattern}/Property/(?P<property>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int, property: str) -> typing.Self:
        """
        Create a new property identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          property: Unique property identifier.

        Returns:
          The created property identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}/Property/{property}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "property": property,
        }

        return identifier

    @property
    def property(self) -> str:
        """Unique property identifier."""

        return self._data["property"]
