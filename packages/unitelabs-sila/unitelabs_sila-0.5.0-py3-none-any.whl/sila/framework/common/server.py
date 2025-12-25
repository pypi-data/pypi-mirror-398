import abc
import asyncio
import dataclasses
import logging

import typing_extensions as typing

from ..identifiers import (
    CommandIdentifier,
    DataTypeIdentifier,
    FeatureIdentifier,
    MetadataIdentifier,
    PropertyIdentifier,
)
from .context import Context

if typing.TYPE_CHECKING:
    from ...server import (
        CommandExecution,
        Metadata,
        ObservableCommand,
        ObservableProperty,
        UnobservableCommand,
        UnobservableProperty,
    )
    from ..command import Command
    from ..data_types import Custom
    from ..property import Property
    from .feature import Feature


@dataclasses.dataclass
class Server(Context):
    """A system (a software system, a laboratory instrument, or device) that offers features to a client."""

    def __init__(self) -> None:
        super().__init__()

        self._ready = asyncio.Event()
        self._shutdown = asyncio.Event()
        self._command_executions: dict[str, "CommandExecution"] = {}

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    @abc.abstractmethod
    async def start(self) -> None:
        """Start this server."""

        if self._ready.is_set():
            msg = f"The {self.__class__.__name__} is already running."
            raise RuntimeError(msg)

        self.logger.info(f"Starting {self.__class__.__name__}...")
        self._shutdown.clear()
        await self._start()
        self._ready.set()

    @abc.abstractmethod
    async def _start(self) -> None:
        """Override this method to implement the start behaviour of the server."""

    @abc.abstractmethod
    async def stop(self, grace: typing.Optional[float] = None) -> None:
        """
        Stop this server.

        Args:
          grace: A grace period in seconds allowing the RPC handlers to
            gracefully shutdown.
        """

        self.logger.info(f"Stopping {self.__class__.__name__}...")
        self._ready.clear()
        self._shutdown.set()
        await self._stop(grace)

    @abc.abstractmethod
    async def _stop(self, grace: typing.Optional[float] = None) -> None:
        """
        Override this method to implement the stop behaviour of the server.

        Args:
          grace: A grace period in seconds allowing the RPC handlers to
            gracefully shutdown.
        """

    async def wait_for_ready(self) -> None:
        """Wait until the server is ready."""

        await self._ready.wait()
        self._ready.clear()

    async def wait_for_termination(self) -> None:
        """Continues current coroutine once the server stops."""

        await self._shutdown.wait()
        self._shutdown.clear()

    @typing.override
    def get_command_execution(self, command_execution_uuid: str) -> "CommandExecution":
        return typing.cast("CommandExecution", super().get_command_execution(command_execution_uuid))

    @typing.override
    def register_feature(self, feature: "Feature") -> None:
        """
        Add a feature as RPC handler with this server.

        Args:
          feature: The SiLA feature to add to this server.
        """

        if self._ready.is_set():
            msg = f"Unable to register feature. The {self.__class__.__name__} is already running."
            raise RuntimeError(msg)

        super().register_feature(feature)

    def get_property(self, identifier: str) -> "Property":
        """
        Get a property by its identifier.

        Args:
          identifier: The fully qualified identifier of the property to
            receive.

        Returns:
          The property registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        identifier = PropertyIdentifier(identifier)

        feature = self.get_feature(identifier)

        if identifier.property not in feature.properties:
            msg = f"Requested unknown property identifier '{identifier}'."
            raise ValueError(msg)

        return feature.properties[identifier.property]

    def get_unobservable_property(self, identifier: str) -> "UnobservableProperty":
        """
        Get an unobservable property by its identifier.

        Args:
          identifier: The fully qualified identifier of the unobservable
            property to receive.

        Returns:
          The unobservable property registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        property_ = self.get_property(identifier)

        from ...server import UnobservableProperty

        if not isinstance(property_, UnobservableProperty):
            msg = "Expected identifier to reference an unobservable property, received 'observable property' instead."
            raise ValueError(msg)

        return property_

    def get_observable_property(self, identifier: str) -> "ObservableProperty":
        """
        Get an observable property by its identifier.

        Args:
          identifier: The fully qualified identifier of the observable
            property to receive.

        Returns:
          The observable property registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        property_ = self.get_property(identifier)

        from ...server import ObservableProperty

        if not isinstance(property_, ObservableProperty):
            msg = "Expected identifier to reference an observable property, received 'unobservable property' instead."
            raise ValueError(msg)

        return property_

    def get_command(self, identifier: str) -> "Command":
        """
        Get a command by its identifier.

        Args:
          identifier: The fully qualified identifier of the command to
            receive.

        Returns:
          The command registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        identifier = CommandIdentifier(identifier)

        feature = self.get_feature(identifier)

        if identifier.command not in feature.commands:
            msg = f"Requested unknown command identifier '{identifier}'."
            raise ValueError(msg)

        return feature.commands[identifier.command]

    def get_unobservable_command(self, identifier: str) -> "UnobservableCommand":
        """
        Get an unobservable command by its identifier.

        Args:
          identifier: The fully qualified identifier of the unobservable
            command to receive.

        Returns:
          The unobservable command registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        command = self.get_command(identifier)

        from ...server import UnobservableCommand

        if not isinstance(command, UnobservableCommand):
            msg = "Expected identifier to reference an unobservable command, received 'observable command' instead."
            raise ValueError(msg)

        return command

    def get_observable_command(self, identifier: str) -> "ObservableCommand":
        """
        Get an observable command by its identifier.

        Args:
          identifier: The fully qualified identifier of the observable
            command to receive.

        Returns:
          The observable command registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        command = self.get_command(identifier)

        from ...server import ObservableCommand

        if not isinstance(command, ObservableCommand):
            msg = "Expected identifier to reference an observable command, received 'unobservable command' instead."
            raise ValueError(msg)

        return command

    def get_data_type_definition(self, identifier: str) -> type["Custom"]:
        """
        Get a custom data type definition by its identifier.

        Args:
          identifier: The fully qualified identifier of the custom data
            type definition to receive.

        Returns:
          The custom data type definition registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        identifier = DataTypeIdentifier(identifier)

        feature = self.get_feature(identifier)

        if identifier.data_type not in feature.data_type_definitions:
            msg = f"Requested unknown custom data type identifier '{identifier}'."
            raise ValueError(msg)

        return feature.data_type_definitions[identifier.data_type]

    def get_metadata(self, identifier: str) -> type["Metadata"]:
        """
        Get metadata by its identifier.

        Args:
          identifier: The fully qualified identifier of the metadata to
            receive.

        Returns:
          The metadata registered with this server.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        identifier = MetadataIdentifier(identifier)

        feature = self.get_feature(identifier)

        if identifier.metadata not in feature.metadata:
            msg = f"Requested unknown metadata identifier '{identifier}'."
            raise ValueError(msg)

        from ...server import Metadata

        metadata = feature.metadata[identifier.metadata]
        assert issubclass(metadata, Metadata)

        return metadata

    def get_metadata_by_affect(self, identifier: str) -> list[type["Metadata"]]:
        """
        Get a list of metadata that affect the given identifier.

        Args:
          identifier: The fully qualified identifier of the feature,
            command or property to check.

        Returns:
          The metadata that affects the given identifier.

        Raises:
          ValueError: If the given identifier is invalid or not
            recognized.
        """

        identifier = FeatureIdentifier(identifier)

        from ...server import Metadata

        return [
            metadata
            for feature in self.features.values()
            for metadata in feature.metadata.values()
            if issubclass(metadata, Metadata)
            and (identifier.feature_identifier in metadata.affects or identifier in metadata.affects)
        ]
