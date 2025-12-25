import functools
import re

import typing_extensions as typing

originator = r"(?P<originator>[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*)"
category = r"(?P<category>[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*)*)"
identifier = r"[A-Z][a-zA-Z0-9]*"
version = r"v(?P<version>\d+)"


class FeatureIdentifier(str):
    """
    Represents a unique identifier for a feature.

    Attributes:
      originator: Organization that created and owns the feature.
      category: Domain or group of the feature.
      feature: Unique feature name.
      version: Major version number.

    Raises:
      ValueError: If the input string does not match the required format.

    Examples:
      >>> identifier = FeatureIdentifier("org.silastandard/core/SiLAService/v1")
    """

    _registry: typing.ClassVar[set[type[typing.Self]]] = set()
    _pattern: typing.ClassVar[str] = rf"{originator}/{category}/(?P<feature>{identifier})/{version}"
    _regex: typing.ClassVar[re.Pattern] = re.compile(_pattern)

    _data: dict[str, typing.Any]

    @typing.override
    def __new__(cls, value: str) -> typing.Self:
        if isinstance(value, cls):
            instance = super().__new__(type(value), value)
            instance._data = value._data

            return instance

        registry = {cls} | cls._registry if cls is FeatureIdentifier else {cls}
        for identifier in registry:
            if match := identifier._regex.fullmatch(value):
                values = match.groupdict()

                if "version" in values:
                    values["version"] = int(values["version"])

                instance = super().__new__(identifier, value)
                instance._data = values

                return instance

        msg = f"Expected fully qualified feature identifier, received '{value}'."
        raise ValueError(msg)

    @typing.override
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._registry.add(cls)

    @classmethod
    def create(cls, originator: str, category: str, feature: str, version: int) -> typing.Self:
        """
        Create a new feature identifier from the given components.

        Args:
          originator: The organization who created and owns the feature.
          category: Group features into domains of application.
          feature: Unique feature identifier.
          version: The major feature version.

        Returns:
          The created feature identifier.
        """

        identifier = super().__new__(cls, f"{originator}/{category}/{feature}/v{version}")
        identifier._data = {
            "originator": originator,
            "category": category,
            "feature": feature,
            "version": version,
        }

        return identifier

    @property
    def originator(self) -> str:
        """The organization who created and owns the feature."""

        return self._data["originator"]

    @property
    def category(self) -> str:
        """Group features into domains of application."""

        return self._data["category"]

    @property
    def feature(self) -> str:
        """Unique feature identifier."""

        return self._data["feature"]

    @property
    def version(self) -> int:
        """The major feature version."""

        return self._data["version"]

    @functools.cached_property
    def feature_identifier(self) -> "FeatureIdentifier":
        """The fully qualified feature identifier."""

        return FeatureIdentifier.create(self.originator, self.category, self.feature, self.version)

    @typing.override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented

        return self.lower() == other.lower()

    @typing.override
    def __ne__(self, other: object) -> bool:
        if not isinstance(other, str):
            return NotImplemented

        return self.lower() != other.lower()

    @typing.override
    def __hash__(self):
        return super().lower().__hash__()

    @typing.override
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"value={super().__str__()!r}, "
            f"{', '.join(f'{key}={value!r}' for key, value in self._data.items())}"
            ")"
        )
