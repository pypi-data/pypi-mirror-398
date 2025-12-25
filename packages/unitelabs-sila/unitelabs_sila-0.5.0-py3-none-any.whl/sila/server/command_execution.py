import asyncio
import functools
import uuid
import weakref

import typing_extensions as typing

from sila import datetime

from .. import framework
from ..framework import (
    CommandConfirmation,
    CommandExecutionInfo,
    CommandExecutionNotFinished,
    CommandExecutionStatus,
    CommandExecutionUUID,
    Duration,
    MetadataIdentifier,
    Native,
    Real,
    Stream,
)

if typing.TYPE_CHECKING:
    from .observable_command import ObservableCommand


T = typing.TypeVar("T", bound=Native)


class CommandExecution(framework.CommandExecution, typing.Generic[T]):
    """Tracks the progress of an observable command execution."""

    def __init__(
        self,
        command: "ObservableCommand",
        parameters: typing.Optional[dict[str, Native]] = None,
        metadata: typing.Optional[dict[MetadataIdentifier, Native]] = None,
        lifetime: typing.Optional[datetime.timedelta] = None,
    ) -> None:
        self._command = weakref.proxy(command)
        self._execute = functools.partial(command.execute, parameters or {}, metadata or {}, command_execution=self)
        self._lifetime = lifetime
        self._result: typing.Optional[bytes] = None
        self._exception: typing.Optional[BaseException] = None
        self._task: typing.Optional[asyncio.Task] = None
        self._running: bool = False

        self.command_execution_uuid = str(uuid.uuid4())
        self.execution_info = Stream[CommandExecutionInfo](maxsize=1)
        self.intermediate_responses = Stream[T](maxsize=1)

        self.execution_info.next(
            CommandExecutionInfo(
                status=CommandExecutionStatus.WAITING,
                progress=Real(0.0),
            )
        )

    @property
    @typing.override
    def command(self) -> "ObservableCommand":
        return self._command

    @property
    def command_confirmation(self) -> CommandConfirmation:
        """A command confirmation message is returned to identify the command execution."""

        return CommandConfirmation(
            command_execution_uuid=CommandExecutionUUID(value=self.command_execution_uuid),
            lifetime_of_execution=Duration.from_total_seconds(self._lifetime.total_seconds())
            if self._lifetime is not None
            else None,
        )

    def execute(self) -> None:
        """Execute the observable command in a background task."""

        if self._task is not None:
            msg = "The command is already executing."
            raise RuntimeError(msg)

        self._task = asyncio.create_task(self._execute())

    def done(self) -> bool:
        """Whether the command execution has a result or an exception set."""

        return self._result is not None or self._exception is not None

    def result(self) -> bytes:
        """
        Return the result of the command execution.

        Returns:
          The result value.

        Raises:
          CommandExecutionNotFinished: If the result isn't yet available.
          BaseException: If the command execution is done and has an
            exception set by the `set_exception()` method.
        """

        if self._exception is not None:
            raise self._exception

        if self._result is None:
            msg = "Result is not ready."
            raise CommandExecutionNotFinished(msg)

        return self._result

    async def set_result(self, result: bytes) -> None:
        """
        Mark the command execution as done and set its result.

        Args:
          result: The result to set.
        """

        if not self._running:
            self.execution_info.next(
                CommandExecutionInfo(
                    status=CommandExecutionStatus.RUNNING,
                    progress=Real(1.0),
                    remaining_time=Duration(),
                )
            )
            await asyncio.sleep(0)

        self._result = result
        self.execution_info.next(
            CommandExecutionInfo(
                status=CommandExecutionStatus.FINISHED_SUCCESSFULLY,
                progress=Real(1.0),
                remaining_time=Duration(),
            )
        )
        self.execution_info.close()
        self.intermediate_responses.close()

    async def set_exception(self, exception: BaseException) -> None:
        """
        Mark the command execution as done and set an exception.

        Args:
          exception: The exception to raise.
        """

        if not self._running:
            self.execution_info.next(
                CommandExecutionInfo(
                    status=CommandExecutionStatus.RUNNING,
                    progress=Real(1.0),
                    remaining_time=Duration(),
                )
            )
            await asyncio.sleep(0)

        self._exception = exception
        self.execution_info.next(
            CommandExecutionInfo(
                status=CommandExecutionStatus.FINISHED_WITH_ERROR,
                progress=Real(1.0),
                remaining_time=Duration(),
            )
        )
        self.execution_info.close()
        self.intermediate_responses.close()

    def update_execution_info(
        self,
        progress: typing.Optional[float] = None,
        remaining_time: typing.Optional[datetime.timedelta] = None,
        updated_lifetime: typing.Optional[datetime.timedelta] = None,
    ) -> None:
        """
        Update the current execution info of the command execution.

        Args:
          progress: The estimated progress in percent (0 ... 100%).
          remaining_time: The estimated remaining execution time.
          updated_lifetime: The duration during which this execution is
            valid.
        """

        if self._lifetime is not None and updated_lifetime is not None and updated_lifetime > self._lifetime:
            self._lifetime = updated_lifetime

        execution_info = CommandExecutionInfo(
            status=CommandExecutionStatus.RUNNING,
            progress=Real(progress) if progress is not None else None,
            remaining_time=Duration.from_total_seconds(remaining_time.total_seconds())
            if remaining_time is not None
            else None,
            updated_lifetime=Duration.from_total_seconds(self._lifetime.total_seconds())
            if self._lifetime is not None
            else None,
        )
        self.execution_info.next(execution_info)
        self._running = True

    def send_intermediate_responses(self, intermediate_responses: T) -> None:
        """Send intermediate responses to the client."""

        self.intermediate_responses.next(intermediate_responses)

    @typing.override
    def cancel(self) -> None:
        if self._task is not None:
            self._task.cancel()

        self.execution_info.close()
        self.intermediate_responses.close()
