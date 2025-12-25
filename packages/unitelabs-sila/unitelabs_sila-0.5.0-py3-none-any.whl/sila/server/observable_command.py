import collections.abc
import dataclasses
import inspect
import logging

import grpc.aio
import typing_extensions as typing

from .. import framework
from ..framework import (
    CommandConfirmation,
    CommandExecutionInfo,
    CommandExecutionUUID,
    ConversionError,
    DecodeError,
    DefinedExecutionError,
    Feature,
    MetadataIdentifier,
    Native,
    Server,
    SiLAError,
    UndefinedExecutionError,
    ValidationError,
)
from .command_execution import CommandExecution


@dataclasses.dataclass
class ObservableCommand(framework.ObservableCommand):
    """Any command for which observing the progress of execution is possible or does make sense."""

    function: typing.Callable = dataclasses.field(repr=False, default=lambda **_: ...)
    """The implementation which is executed by the RPC handler."""

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    async def initiate(
        self, request: bytes = b"", metadata: typing.Optional[dict[str, bytes]] = None
    ) -> "CommandConfirmation":
        """
        Initiate the execution of  the command.

        Args:
          request: Input parameters passed to the command.
          metadata: Additional metadata sent from client to server.

        Returns:
          Confirmation that the command execution has been accepted.

        Raises:
          NoMetadataAllowed: If providing metadata is not allowed.
          InvalidMetadata: If metadata is missing or invalid.
          CommandExecutionNotAccepted: If the server does not allow
            further command executions.
          ValidationError: If command parameters are missing or invalid.
          DefinedExecutionError: If metadata handling results in a
            defined execution error
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        try:
            # Metadata
            parsed_metadata = dict[MetadataIdentifier, Native]()
            for interceptor in self.feature.context.get_metadata_by_affect(self.fully_qualified_identifier):
                metadatum = await interceptor.from_buffer(self, metadata)
                parsed_metadata.update(await metadatum.intercept(self))

            # Parameters
            try:
                parameters = await self.feature.context.protobuf.decode(
                    f"{self.feature.rpc_package}.{self.identifier}_Parameters", request
                )
            except DecodeError as error:
                raise ValidationError(
                    parameter=f"{self.fully_qualified_identifier}/Parameter/{error.path[0]}", message=error.message
                ) from error
            except ConversionError as error:
                raise ValidationError(
                    parameter=f"{self.fully_qualified_identifier}/Parameter/{error.path[0]}", message=error.message
                ) from error

            # Execute
            command_execution = CommandExecution(command=self, parameters=parameters, metadata=parsed_metadata)
            self.feature.context.add_command_execution(command_execution)
            command_execution.execute()

            return command_execution.command_confirmation
        except DefinedExecutionError as error:
            error = error.with_feature(self.feature.fully_qualified_identifier)
            raise error

    async def initiate_rpc_handler(self, request: bytes, context: grpc.aio.ServicerContext) -> bytes:
        """
        Handle the gRPC call to initiate the execution of the command.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          Confirmation that the command execution has been accepted.
        """

        try:
            metadata: dict[str, bytes] = {
                key: value
                for key, value in context.invocation_metadata() or ()
                if key.startswith("sila-") and key.endswith("-bin") and isinstance(value, bytes)
            }

            command_confirmation = await self.initiate(request, metadata)
            return command_confirmation.encode()
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    async def subscribe_status(
        self, command_execution_uuid: str
    ) -> collections.abc.AsyncIterator["CommandExecutionInfo"]:
        """
        Subscribe to status changes of the command execution.

        Args:
          command_execution_uuid: The unique identifier of the command
            execution.

        Yields:
          The current status of the command execution.

        Raises:
          InvalidCommandExecutionUUID: If the given identifier is invalid
            or not recognized.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        command_execution: CommandExecution = self.feature.context.get_command_execution(command_execution_uuid)

        async for status in command_execution.execution_info:
            yield status

    async def subscribe_status_rpc_handler(
        self, request: bytes, context: grpc.aio.ServicerContext
    ) -> collections.abc.AsyncIterator[bytes]:
        """
        Handle the gRPC call to subscribe to status changes of the command execution.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          The current status of the command execution.
        """

        try:
            command_execution_uuid = CommandExecutionUUID.decode(request).value
            async for value in self.subscribe_status(command_execution_uuid):
                yield value.encode()
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    async def subscribe_intermediate(self, command_execution_uuid: str) -> collections.abc.AsyncIterator[bytes]:
        """
        Subscribe to intermediate responses of the command execution.

        Args:
          command_execution_uuid: The unique identifier of the command
            execution.

        Yields:
          The current intermediate responses of the command execution.

        Raises:
          InvalidCommandExecutionUUID: If the given identifier is invalid
            or not recognized.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        command_execution: CommandExecution = self.feature.context.get_command_execution(command_execution_uuid)

        async for intermediate_responses in command_execution.intermediate_responses:
            yield await self.feature.context.protobuf.encode(
                f"{self.feature.rpc_package}.{self.identifier}_IntermediateResponses", intermediate_responses
            )

    async def subscribe_intermediate_rpc_handler(
        self, request: bytes, context: grpc.aio.ServicerContext
    ) -> collections.abc.AsyncIterator[bytes]:
        """
        Handle the gRPC call to subscribe to intermediate responses of the command execution.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          The current intermediate responses of the command execution.
        """

        try:
            command_execution_uuid = CommandExecutionUUID.decode(request).value
            async for value in self.subscribe_intermediate(command_execution_uuid):
                yield value
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    async def get_result(self, command_execution_uuid: str) -> bytes:
        """
        Get the responses of the command execution.

        Args:
          command_execution_uuid: The unique identifier of the command
            execution.

        Returns:
          The resulting responses of the command execution.

        Raises:
          InvalidCommandExecutionUUID: If the given identifier is invalid
            or not recognized.
          CommandExecutionNotFinished: If the command execution has not
            been finished yet.
          DefinedExecutionError: If command execution resulted in a
            defined execution error
          UnefinedExecutionError: If command execution resulted in an
            undefined execution error.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        command_execution: CommandExecution = self.feature.context.get_command_execution(command_execution_uuid)
        return command_execution.result()

    async def get_result_rpc_handler(self, request: bytes, context: grpc.aio.ServicerContext) -> bytes:
        """
        Handle the gRPC call to get the responses of the command execution.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          The resulting responses of the command execution.
        """

        try:
            command_execution_uuid = CommandExecutionUUID.decode(request).value
            return await self.get_result(command_execution_uuid)
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    async def execute(
        self,
        parameters: dict[str, Native],
        metadata: dict[MetadataIdentifier, Native],
        command_execution: CommandExecution,
    ) -> None:
        """
        Execute the command.

        Args:
          parameters: Input parameters passed to the command.
          metadata: Additional metadata sent from client to server.
          command_execution: The command execution instance.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        try:
            responses = self.function(**parameters, metadata=metadata, command_execution=command_execution)

            if inspect.isawaitable(responses):
                responses = await responses

            message = await self.feature.context.protobuf.encode(
                f"{self.feature.rpc_package}.{self.identifier}_Responses", responses
            )
            await command_execution.set_result(message)
        except SiLAError as error:
            if isinstance(error, DefinedExecutionError) and error._identifier is None:
                error = error.with_feature(self.feature.fully_qualified_identifier)

            await command_execution.set_exception(error)
        except Exception as error:
            self.logger.exception(error)
            await command_execution.set_exception(UndefinedExecutionError(str(error)))

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=self.identifier + "_Parameters", message=self.parameters, package=feature.rpc_package
        )
        feature.context.protobuf.register_message(
            name=self.identifier + "_Responses", message=self.responses, package=feature.rpc_package
        )
        if self.intermediate_responses:
            feature.context.protobuf.register_message(
                name=self.identifier + "_IntermediateResponses",
                message=self.intermediate_responses,
                package=feature.rpc_package,
            )

        services = {
            self.identifier: grpc.unary_unary_rpc_method_handler(self.initiate_rpc_handler),
            f"{self.identifier}_Info": grpc.unary_stream_rpc_method_handler(self.subscribe_status_rpc_handler),
            f"{self.identifier}_Result": grpc.unary_unary_rpc_method_handler(self.get_result_rpc_handler),
        }
        if self.intermediate_responses:
            services[f"{self.identifier}_Intermediate"] = grpc.unary_stream_rpc_method_handler(
                self.subscribe_intermediate_rpc_handler
            )

        feature.context.protobuf.register_service(feature.identifier, services, package=feature.rpc_package)

        return self
