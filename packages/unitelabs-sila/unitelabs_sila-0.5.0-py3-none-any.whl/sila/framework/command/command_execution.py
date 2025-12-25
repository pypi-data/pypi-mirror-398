import typing_extensions as typing

if typing.TYPE_CHECKING:
    from .observable_command import ObservableCommand


class CommandExecution(typing.Protocol):
    """Tracks the progress of an observable command execution."""

    command_execution_uuid: str
    """Uniquely identifies the Command execution."""

    command: "ObservableCommand"
    """The observable command being executed."""

    def cancel(self) -> None:
        """Cancel the ongoing command execution."""
