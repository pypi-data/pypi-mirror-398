import typing_extensions as typing

from ..protobuf import Protobuf
from .context import Context

if typing.TYPE_CHECKING:
    from ..binary_transfer import BinaryTransferHandler
    from ..command import CommandExecution
    from ..identifiers import FeatureIdentifier
    from .feature import Feature


class ContextProxy(Context):
    """Mimics a real context object to enable lazy loading."""

    def __init__(self) -> None:
        self._context: typing.Optional[Context] = None
        self._protobuf: Protobuf = Protobuf(self)
        self._features: dict["FeatureIdentifier", "Feature"] = {}
        self._command_executions: dict[str, "CommandExecution"] = {}

    @property
    def protobuf(self) -> Protobuf:
        """A collection of protobuf messages and services."""

        if self._context:
            return self._context.protobuf

        return self._protobuf

    @property
    def features(self) -> dict["FeatureIdentifier", "Feature"]:
        """A collection of registered features."""

        if self._context:
            return self._context.features

        return self._features

    @property
    def command_executions(self) -> dict[str, "CommandExecution"]:
        """A collection of currently executed commands."""

        if self._context:
            return self._context.command_executions

        return self._command_executions

    @property
    def binary_transfer_handler(self) -> "BinaryTransferHandler":
        """Upload and download large binaries in chunks."""

        if self._context:
            return self._context.binary_transfer_handler

        msg = "Unable to access 'BinaryTransferHandler' on unbound 'Feature'."
        raise RuntimeError(msg)

    @property
    def context(self) -> typing.Optional[Context]:
        """The lazily loaded context that is protected by this proxy."""

        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        context._features |= self._features
        context._protobuf.merge(self._protobuf)
        self._context = context

    @typing.override
    def register_feature(self, feature: "Feature") -> None:
        if self.context is not None:
            self.context.register_feature(feature)
        else:
            self._features[feature.fully_qualified_identifier] = feature

    @typing.override
    def add_command_execution(self, command_execution: "CommandExecution") -> None:
        if self.context is not None:
            self.context.add_command_execution(command_execution)
        else:
            self._command_executions[command_execution.command_execution_uuid] = command_execution

    @typing.override
    def get_command_execution(self, command_execution_uuid: str) -> "CommandExecution":
        try:
            return self.command_executions[command_execution_uuid]
        except KeyError:
            msg = f"Could not find any execution with the given uuid '{command_execution_uuid}'."
            raise ValueError(msg) from None
