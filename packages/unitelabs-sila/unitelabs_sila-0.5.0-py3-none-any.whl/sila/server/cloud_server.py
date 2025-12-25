import asyncio
import contextlib
import dataclasses
import functools
import logging
import types
import weakref

import grpc
import grpc.aio
import typing_extensions as typing

from ..framework import (
    BinaryTransferError,
    ChannelOptions,
    ClientMessage,
    CloudMetadata,
    CommandConfirmationResponse,
    CommandExecutionResponse,
    CommandExecutionUUID,
    DecodeError,
    EncodeError,
    InvalidCommandExecutionUUID,
    MetadataResponse,
    ObservableCommandResponse,
    PropertyResponse,
    Server,
    ServerMessage,
    SiLAError,
    Stream,
    UndefinedExecutionError,
    UnobservableCommandResponse,
    create_channel,
)
from .binary_transfer_handler import ServerBinaryTransferHandler

if typing.TYPE_CHECKING:
    from ..framework import Feature, FeatureIdentifier, Protobuf
    from .command_execution import CommandExecution


@dataclasses.dataclass
class CloudServerConfig:
    """Configuration to run a SiLA 2 cloud server."""

    hostname: str = "localhost"
    """The target hostname to connect to."""

    port: int = 50_000
    """The target port to connect to."""

    tls: bool = True
    """
    Whether to run a secure/TLS channel or a plaintext channel (i.e.
    no TLS), defaults to run with TLS encryption.
    """

    root_certificates: typing.Optional[bytes] = None
    """
    The PEM-encoded root certificates as a byte string, or None to
    retrieve them from a default location chosen by gRPC runtime.
    """

    certificate_chain: typing.Optional[bytes] = None
    """
    The PEM-encoded certificate chain as a byte string to use or None
    if no certificate chain should be used.
    """

    private_key: typing.Optional[bytes] = None
    """
    The PEM-encoded private key as a byte string, or None if no
    private key should be used.
    """

    reconnect_delay: float = 10_000.0
    """
    The time in ms to wait before reconnecting the channel after an
    error occurs.
    """

    options: ChannelOptions = dataclasses.field(default_factory=ChannelOptions)
    """
    Additional options for the underlying gRPC connection.
    """


class CloudServer(Server):
    """
    A SiLA 2 cloud server capable of using the server-initiated connection method.

    Args:
      target: The target address to connect to.
      options: Additional options for the connection.
    """

    def __init__(self, config: typing.Optional[typing.Union[dict, CloudServerConfig]] = None, /):
        super().__init__()
        self._context: Server = weakref.proxy(self)
        self._binary_transfer_handler: "ServerBinaryTransferHandler" = ServerBinaryTransferHandler(self)

        if isinstance(config, dict):
            import warnings

            warnings.warn(
                "Providing CloudServerConfig as a dictionary is deprecated and will be removed in a future release. "
                "Please provide a CloudServerConfig instance instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            self._config = CloudServerConfig(**config)
        else:
            self._config = config or CloudServerConfig()

        self._channel: typing.Optional[grpc.aio.Channel] = None
        self._responses = Stream[ServerMessage]()
        self._shutdown = asyncio.Event()
        self._rpc_handler: typing.Optional[asyncio.Task] = None
        self._tasks: dict[str, asyncio.Task] = {}

    @property
    def context(self) -> typing.Optional[Server]:
        """The context."""

        return self._context

    @context.setter
    def context(self, context: Server) -> None:
        self._context = weakref.proxy(context)

    @property
    @typing.override
    def protobuf(self) -> "Protobuf":
        return self._context._protobuf

    @property
    @typing.override
    def features(self) -> dict["FeatureIdentifier", "Feature"]:
        return self._context._features

    @property
    @typing.override
    def command_executions(self) -> dict[str, "CommandExecution"]:
        return self._context._command_executions

    @property
    @typing.override
    def binary_transfer_handler(self) -> "ServerBinaryTransferHandler":
        return self._context._binary_transfer_handler

    @property
    def tasks(self) -> dict[str, asyncio.Task]:
        """The currently ongoing tasks."""

        return self._tasks

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    @typing.override
    async def _start(self) -> None:
        await super()._start()

        try:
            self._responses = Stream[ServerMessage]()
            target = f"{self._config.hostname}:{self._config.port}"
            self._channel = await functools.partial(create_channel, **dataclasses.asdict(self._config))(target)
            self.logger.info(f"{self.__class__.__name__} connected to '{target}'.")

            listen = self._channel.stream_stream(
                method="/sila2.org.silastandard.CloudClientEndpoint/ConnectSiLAServer",
                request_serializer=self._serialize_request,
                response_deserializer=self._deserialize_response,
            )
            request_iterator: grpc.aio.StreamStreamCall[ServerMessage, ClientMessage] = listen(
                request_iterator=self._responses, wait_for_ready=True
            )
            self._rpc_handler = asyncio.create_task(self.rpc_handler(request_iterator))
        except grpc.aio.AioRpcError as error:
            self.logger.error(error)
            await self.stop()

    async def rpc_handler(self, request_iterator: grpc.aio.StreamStreamCall[ServerMessage, ClientMessage]) -> None:
        """
        Handle the bidirectional gRPC call between cloud server and client.

        Args:
          request_iterator: The cloud client's client message.
        """

        try:
            async for response in request_iterator:
                await self.receive(response)
        except asyncio.CancelledError:
            pass
        except grpc.aio.AioRpcError as error:
            self.logger.error(error)

            await self.stop()
            await asyncio.sleep(self._config.reconnect_delay / 1000)
            await self.start()

    @typing.override
    async def _stop(self, grace: typing.Optional[float] = None) -> None:
        await super()._stop(grace)

        for task in self._tasks.values():
            task.cancel()

        if self._rpc_handler and self._rpc_handler != asyncio.current_task():
            self._rpc_handler.cancel()
            self._rpc_handler = None

        if self._channel:
            await self._channel.close(grace=grace)
            self._channel = None

    async def receive(self, message: ClientMessage) -> None:
        """
        Receive and handle a client message.

        Args:
          message: The cloud client's request to handle.
        """

        self.logger.debug("> %s", message)

        message_type: str = ""
        coroutine: typing.Optional[types.CoroutineType[typing.Any, typing.Any, None]] = None

        if message.unobservable_command_execution is not None:
            message_type = "unobservable_command_execution"
            coroutine = self.unobservable_command_execution(
                message.request_uuid,
                message.unobservable_command_execution.fully_qualified_command_id,
                message.unobservable_command_execution.command_parameter.parameters,
                self._parse_metadata(message.unobservable_command_execution.command_parameter.metadata),
            )

        elif message.observable_command_initiation is not None:
            message_type = "observable_command_initiation"
            coroutine = self.observable_command_initiation(
                message.request_uuid,
                message.observable_command_initiation.fully_qualified_command_id,
                message.observable_command_initiation.command_parameter.parameters,
                self._parse_metadata(message.observable_command_initiation.command_parameter.metadata),
            )

        elif message.observable_command_execution_info is not None:
            message_type = "observable_command_execution_info"
            coroutine = self.observable_command_execution_info_subscription(
                message.request_uuid,
                message.observable_command_execution_info.command_execution_uuid,
            )

        elif message.observable_command_intermediate_response is not None:
            message_type = "observable_command_intermediate_response"
            coroutine = self.observable_command_intermediate_response_subscription(
                message.request_uuid,
                message.observable_command_intermediate_response.command_execution_uuid,
            )

        elif message.observable_command_response is not None:
            message_type = "observable_command_get_response"
            coroutine = self.observable_command_get_response(
                message.request_uuid,
                message.observable_command_response.command_execution_uuid,
            )

        elif message.metadata_request is not None:
            affected_calls = []

            with contextlib.suppress(ValueError):
                metadata = self._context.get_metadata(message.metadata_request.fully_qualified_metadata_id)
                affected_calls = metadata.affects

            msg = ServerMessage(
                request_uuid=message.request_uuid,
                get_fcp_affected_by_metadata_response=MetadataResponse(affected_calls),
            )
            await self.respond(msg)

        elif message.unobservable_property_read is not None:
            message_type = "unobservable_property_read"
            coroutine = self.unobservable_property_read(
                message.request_uuid,
                message.unobservable_property_read.fully_qualified_property_id,
                self._parse_metadata(message.unobservable_property_read.metadata),
            )

        elif message.observable_property_subscription is not None:
            message_type = "observable_property_subscription"
            coroutine = self.observable_property_subscription(
                message.request_uuid,
                message.observable_property_subscription.fully_qualified_property_id,
                self._parse_metadata(message.observable_property_subscription.metadata),
            )

        elif message.cancel_observable_command_execution_info is not None:
            await self.cancel_observable_command_execution_info_subscription(
                message.request_uuid,
            )

        elif message.cancel_observable_command_intermediate_response is not None:
            await self.cancel_observable_command_intermediate_response_subscription(
                message.request_uuid,
            )

        elif message.cancel_observable_property is not None:
            await self.cancel_observable_property_subscription(message.request_uuid)

        elif message.create_binary_upload_request is not None:
            try:
                response = await self._binary_transfer_handler.create_binary(
                    message.create_binary_upload_request.create_binary_request,
                    self._parse_metadata(message.create_binary_upload_request.metadata),
                )
                msg = ServerMessage(request_uuid=message.request_uuid, create_binary_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)
            except SiLAError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, command_error=error)
                await self.respond(msg)

        elif message.upload_chunk_request is not None:
            try:
                response = await self._binary_transfer_handler.upload_chunk(message.upload_chunk_request)
                msg = ServerMessage(request_uuid=message.request_uuid, upload_chunk_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)

        elif message.delete_uploaded_binary_request is not None:
            try:
                response = await self._binary_transfer_handler.delete_binary(message.delete_uploaded_binary_request)
                msg = ServerMessage(request_uuid=message.request_uuid, delete_binary_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)

        elif message.get_binary_info_request is not None:
            try:
                response = await self._binary_transfer_handler.get_binary_info(message.get_binary_info_request)
                msg = ServerMessage(request_uuid=message.request_uuid, get_binary_info_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)

        elif message.download_chunk_request is not None:
            try:
                response = await self._binary_transfer_handler.download_chunk(message.download_chunk_request)
                msg = ServerMessage(request_uuid=message.request_uuid, download_chunk_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)

        elif message.delete_downloaded_binary_request is not None:
            try:
                response = await self._binary_transfer_handler.delete_binary(message.delete_downloaded_binary_request)
                msg = ServerMessage(request_uuid=message.request_uuid, delete_binary_response=response)
                await self.respond(msg)
            except BinaryTransferError as error:
                msg = ServerMessage(request_uuid=message.request_uuid, binary_transfer_error=error)
                await self.respond(msg)

        if coroutine is not None:
            task_name = f"{message.request_uuid}_{message_type}"
            self._tasks[task_name] = asyncio.create_task(coroutine, name=task_name)
            self._tasks[task_name].add_done_callback(lambda _: self._tasks.pop(task_name))

    async def respond(self, message: ServerMessage) -> None:
        """
        Respond with a server message.

        Args:
          message: The cloud client's response to answer with.
        """

        self.logger.debug("< %s", message)
        self._responses.next(message)

    async def unobservable_command_execution(
        self, request_uuid: str, identifier: str, parameters: bytes, metadata: dict[str, bytes]
    ) -> None:
        """
        Execute an unobservable command.

        Args:
          request_uuid: A unique identifier for the request.
          identifier: The fully qualified identifier of the unobservable
            command to be executed.
          parameters: Input parameters provided to command execution.
          metadata: Additional metadata required for processing the
            request.
        """

        try:
            unobservable_command = self._context.get_unobservable_command(identifier)
        except ValueError as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=UndefinedExecutionError(str(error)))
            await self.respond(msg)
            return

        try:
            responses = await unobservable_command.execute(parameters, metadata)
        except SiLAError as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)
        else:
            msg = ServerMessage(
                request_uuid=request_uuid,
                unobservable_command_response=UnobservableCommandResponse(response=responses),
            )
            await self.respond(msg)

    async def observable_command_initiation(
        self, request_uuid: str, identifier: str, parameters: bytes, metadata: dict[str, bytes]
    ) -> None:
        """
        Initiate an observable command.

        Args:
          request_uuid: A unique identifier for the request.
          identifier: The fully qualified identifier of the observable
            command to be initiated.
          parameters: Input parameters provided to command execution.
          metadata: Additional metadata required for processing the
            request.
        """

        try:
            observable_command = self._context.get_observable_command(identifier)
        except ValueError as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=UndefinedExecutionError(str(error)))
            await self.respond(msg)
            return

        try:
            command_confirmation = await observable_command.initiate(parameters, metadata)
        except SiLAError as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)
        else:
            msg = ServerMessage(
                request_uuid=request_uuid,
                observable_command_confirmation=CommandConfirmationResponse(command_confirmation=command_confirmation),
            )
            await self.respond(msg)

    async def observable_command_execution_info_subscription(
        self, request_uuid: str, command_execution_uuid: CommandExecutionUUID
    ) -> None:
        """
        Subscribe the execution info of an observable command execution.

        Args:
          request_uuid: A unique identifier for the request.
          command_execution_uuid: The unique identifier of the observable
            command execution to subscribe info for.
        """

        try:
            command_execution = self._context.get_command_execution(command_execution_uuid.value)
        except InvalidCommandExecutionUUID as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)
            return

        observable_command = command_execution.command
        async for status in observable_command.subscribe_status(command_execution.command_execution_uuid):
            msg = ServerMessage(
                request_uuid=request_uuid,
                observable_command_execution_info=CommandExecutionResponse(
                    command_execution_uuid=CommandExecutionUUID(value=command_execution.command_execution_uuid),
                    execution_info=status,
                ),
            )
            await self.respond(msg)

    async def cancel_observable_command_execution_info_subscription(self, request_uuid: str) -> None:
        """
        Cancel the subscription of command execution info.

        Args:
          request_uuid: The unique identifier associated with the
            subscription request.
        """

        if f"{request_uuid}_observable_command_execution_info" in self._tasks:
            self._tasks.pop(f"{request_uuid}_observable_command_execution_info").cancel()

    async def observable_command_intermediate_response_subscription(
        self, request_uuid: str, command_execution_uuid: CommandExecutionUUID
    ) -> None:
        """
        Subscribe the intermediate responses of an observable command execution.

        Args:
          request_uuid: A unique identifier for the request.
          command_execution_uuid: The unique identifier of the observable
            command execution to subscribe responses for.
        """

        try:
            command_execution = self._context.get_command_execution(command_execution_uuid.value)
        except InvalidCommandExecutionUUID as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)
            return

        observable_command = command_execution.command
        async for responses in observable_command.subscribe_intermediate(command_execution.command_execution_uuid):
            msg = ServerMessage(
                request_uuid=request_uuid,
                observable_command_intermediate_response=ObservableCommandResponse(
                    command_execution_uuid=CommandExecutionUUID(value=command_execution.command_execution_uuid),
                    response=responses,
                ),
            )
            await self.respond(msg)

    async def cancel_observable_command_intermediate_response_subscription(self, request_uuid: str) -> None:
        """
        Cancel the subscription of command intermediate responses.

        Args:
          request_uuid: The unique identifier associated with the
            subscription request.
        """

        if f"{request_uuid}_observable_command_intermediate_response" in self._tasks:
            self._tasks.pop(f"{request_uuid}_observable_command_intermediate_response").cancel()

    async def observable_command_get_response(
        self, request_uuid: str, command_execution_uuid: CommandExecutionUUID
    ) -> None:
        """
        Get the response of an observable command.

        Args:
          request_uuid: A unique identifier for the request.
          command_execution_uuid: The unique identifier of the observable
            command execution to get responses for.
        """

        try:
            command_execution = self._context.get_command_execution(command_execution_uuid.value)
        except InvalidCommandExecutionUUID as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)
            return

        try:
            observable_command = command_execution.command
            response = await observable_command.get_result(command_execution.command_execution_uuid)

            msg = ServerMessage(
                request_uuid=request_uuid,
                observable_command_response=ObservableCommandResponse(
                    command_execution_uuid=CommandExecutionUUID(value=command_execution.command_execution_uuid),
                    response=response,
                ),
            )
            await self.respond(msg)
        except SiLAError as error:
            msg = ServerMessage(request_uuid=request_uuid, command_error=error)
            await self.respond(msg)

    async def unobservable_property_read(self, request_uuid: str, identifier: str, metadata: dict[str, bytes]) -> None:
        """
        Read an unobservable property.

        Args:
          request_uuid: A unique identifier for the request.
          identifier: The fully qualified identifier of the unobservable
            property to be read.
          metadata: Additional metadata required for processing the
            request.
        """

        try:
            unobservable_property = self._context.get_unobservable_property(identifier)
        except ValueError as error:
            msg = ServerMessage(request_uuid=request_uuid, property_error=UndefinedExecutionError(str(error)))
            await self.respond(msg)
            return

        try:
            responses = await unobservable_property.read(metadata)
        except SiLAError as error:
            msg = ServerMessage(request_uuid=request_uuid, property_error=error)
            await self.respond(msg)
        else:
            msg = ServerMessage(
                request_uuid=request_uuid,
                unobservable_property_value=PropertyResponse(value=responses),
            )
            await self.respond(msg)

    async def observable_property_subscription(
        self, request_uuid: str, identifier: str, metadata: dict[str, bytes]
    ) -> None:
        """
        Subscribe an observable property.

        Args:
          request_uuid: A unique identifier for the request.
          identifier: The fully qualified identifier of the observable
            property to be subscribed.
          metadata: Additional metadata required for processing the
            request.
        """

        try:
            observable_property = self._context.get_observable_property(identifier)
        except ValueError as error:
            msg = ServerMessage(request_uuid=request_uuid, property_error=UndefinedExecutionError(str(error)))
            await self.respond(msg)
            return

        try:
            async for responses in observable_property.subscribe(metadata):
                message = ServerMessage(
                    request_uuid=request_uuid,
                    observable_property_value=PropertyResponse(value=responses),
                )
                await self.respond(message)

        except SiLAError as error:
            message = ServerMessage(request_uuid=request_uuid, property_error=error)
            await self.respond(message)

    async def cancel_observable_property_subscription(self, request_uuid: str) -> None:
        """
        Cancel the subscription of an observable property.

        Args:
          request_uuid: The unique identifier associated with the
            subscription request.
        """

        if f"{request_uuid}_observable_property_subscription" in self._tasks:
            self._tasks.pop(f"{request_uuid}_observable_property_subscription").cancel()

    def _serialize_request(self, message: ServerMessage) -> bytes:
        try:
            return message.encode()
        except EncodeError as error:
            self.logger.error(error)
            return b""

    def _deserialize_response(self, buffer: bytes) -> ClientMessage:
        try:
            return ClientMessage.decode(buffer)
        except DecodeError as error:
            self.logger.error(error)
            return ClientMessage()

    def _parse_metadata(self, metadata: list[CloudMetadata]) -> dict[str, bytes]:
        return {
            f"sila-{metadata.fully_qualified_metadata_id.replace('/', '-').lower()}-bin": metadata.value
            for metadata in metadata
        }
