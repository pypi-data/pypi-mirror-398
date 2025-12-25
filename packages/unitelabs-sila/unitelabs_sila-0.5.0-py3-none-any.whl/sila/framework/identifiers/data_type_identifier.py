import re

import typing_extensions as typing

from .feature_identifier import FeatureIdentifier, identifier


class DataTypeIdentifier(FeatureIdentifier):
    """
    Uniquely identifies a custom data type among all potentially existing data types.

    Attributes:
      data_type: Unique custom data type identifier.

    Examples:
      >>> identifier = FeatureIdentifier(
      ...     "org.silastandard/core/ErrorRecoveryService/v1/DataType/ContinuationOption"
      ... )
    """

    _pattern: typing.ClassVar[str] = f"{FeatureIdentifier._pattern}/DataType/(?P<data_type>{identifier})"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern, re.IGNORECASE)

    @typing.override
    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int, data_type: str) -> typing.Self:
        """
        Create a new custom data type identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.
          data_type: Unique custom data type identifier.

        Returns:
          The created custom data type identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}/DataType/{data_type}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
            "data_type": data_type,
        }

        return identifier

    @property
    def data_type(self) -> str:
        """Unique custom data type identifier."""

        return self._data["data_type"]
