import dataclasses
import functools
import weakref

import typing_extensions as typing

from ..validators import check_display_name, check_identifier

if typing.TYPE_CHECKING:
    from ..errors import DefinedExecutionError
    from ..identifiers import FeatureIdentifier
    from .feature import Feature


@dataclasses.dataclass
class Handler:
    """Abstract base class for RPC handlers."""

    identifier: str = ""
    """Uniquely identifies the handler within the scope of the same feature."""

    display_name: str = ""
    """Human readable name of the handler."""

    description: str = ""
    """Describes the use and purpose of the handler."""

    errors: dict[str, type["DefinedExecutionError"]] = dataclasses.field(default_factory=dict)
    """
    A list of defined execution errors that can happen when accessing
    this handler.
    """

    feature: typing.Optional["Feature"] = None
    """The SiLA feature this handler was registered with."""

    def __post_init__(self) -> None:
        check_identifier(self.identifier)
        check_display_name(self.display_name)

        if self.feature is not None:
            self.add_to_feature(self.feature)

    @functools.cached_property
    def fully_qualified_identifier(self) -> "FeatureIdentifier":
        """Uniquely identifies the handler."""

        if self.feature is None:
            msg = (
                f"Unable to get fully qualified identifier for {self.__class__.__name__} "
                f"'{self.identifier}' without feature association."
            )
            raise RuntimeError(msg)

        return self.feature.fully_qualified_identifier

    def add_to_feature(self, feature: "Feature") -> typing.Self:
        """
        Register this handler with a feature.

        Args:
          feature: The feature to add this handler to.

        Returns:
          The instance, allowing for method chaining.
        """

        self.feature = weakref.proxy(feature)
        for error in self.errors.values():
            error.add_to_feature(feature)

        return self
