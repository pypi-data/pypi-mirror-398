import collections.abc
import uuid
import weakref

import grpc
import grpc.aio
import typing_extensions as typing

from ..framework.binary_transfer import (
    BinaryDownloadFailed,
    BinaryTransfer,
    BinaryTransferError,
    BinaryTransferHandler,
    BinaryUploadFailed,
    CreateBinaryRequest,
    CreateBinaryResponse,
    DeleteBinaryRequest,
    DeleteBinaryResponse,
    DownloadChunkRequest,
    DownloadChunkResponse,
    GetBinaryInfoRequest,
    GetBinaryInfoResponse,
    InvalidBinaryTransferUUID,
    UploadChunkRequest,
    UploadChunkResponse,
)
from ..framework.data_types import Binary, Constrained, Custom, DataType, Duration, List, Structure
from ..framework.errors import SiLAError
from ..framework.identifiers import ParameterIdentifier

if typing.TYPE_CHECKING:
    from ..framework.common import Execution, Server


class ServerBinaryTransferHandler(BinaryTransferHandler):
    """
    Handle the transfer of large binaries on the server side.

    Args:
      context: The server this handler will be attached to.
    """

    def __init__(self, context: "Server"):
        self._binaries: dict[str, BinaryTransfer] = {}
        self._context: "Server" = weakref.proxy(context)

        self.add_to_server(self._context)

    @property
    def context(self) -> "Server":
        """The context in which the binary transfer handler is applied."""

        return self._context

    @typing.override
    async def get_binary(self, binary_transfer_uuid: str) -> bytes:
        binary = self.get_binary_by_uuid(binary_transfer_uuid)

        if not binary.is_completed:
            msg = f"Requested incomplete Binary with 'binary_transfer_uuid' of '{binary_transfer_uuid}'."
            raise ValueError(msg)

        return binary.buffer

    @typing.override
    async def set_binary(self, value: bytes, execution: typing.Optional["Execution"] = None) -> str:
        binary = BinaryTransfer.from_buffer(value)
        self._binaries[binary.binary_transfer_uuid] = binary

        return binary.binary_transfer_uuid

    def add_to_server(self, server: "Server") -> None:
        """
        Add the necessary grpc handlers to the given server.

        Args:
          server: The server to attach the handlers to.
        """

        server.protobuf.register_service(
            "BinaryUpload",
            {
                "CreateBinary": grpc.unary_unary_rpc_method_handler(
                    self._create_binary,
                    request_deserializer=lambda x: CreateBinaryRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
                "UploadChunk": grpc.stream_stream_rpc_method_handler(
                    self._upload_chunk,
                    request_deserializer=lambda x: UploadChunkRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
                "DeleteBinary": grpc.unary_unary_rpc_method_handler(
                    self._delete_binary,
                    request_deserializer=lambda x: DeleteBinaryRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
            },
            package="sila2.org.silastandard",
        )
        server.protobuf.register_service(
            "BinaryDownload",
            {
                "GetBinaryInfo": grpc.unary_unary_rpc_method_handler(
                    self._get_binary_info,
                    request_deserializer=lambda x: GetBinaryInfoRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
                "GetChunk": grpc.stream_stream_rpc_method_handler(
                    self._download_chunk,
                    request_deserializer=lambda x: DownloadChunkRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
                "DeleteBinary": grpc.unary_unary_rpc_method_handler(
                    self._delete_binary,
                    request_deserializer=lambda x: DeleteBinaryRequest.decode(x),
                    response_serializer=lambda x: x.encode(),
                ),
            },
            package="sila2.org.silastandard",
        )

    async def create_binary(
        self, request: CreateBinaryRequest, metadata: typing.Optional[dict[str, bytes]] = None
    ) -> CreateBinaryResponse:
        """
        Create a new binary transfer session.

        Args:
          request: The client's request to create a new binary.
          metadata: Additional metadata sent from client to server.

        Returns:
          Information about the newly created binary.

        Raises:
          BinaryUploadFailed: If an error occurs during creation.
        """

        try:
            identifier = ParameterIdentifier(request.parameter_identifier)
        except ValueError:
            msg = f"Expected a valid fully qualified parameter identifier, received '{request.parameter_identifier}'."
            raise BinaryUploadFailed(msg) from None

        try:
            command = self.context.get_command(identifier)
            parameter = next(
                parameter for parameter in command.parameters.values() if parameter.identifier == identifier.parameter
            )
        except (KeyError, ValueError, StopIteration):
            msg = f"Expected a known fully qualified parameter identifier, received '{request.parameter_identifier}'."
            raise BinaryUploadFailed(msg) from None

        for interceptor in self.context.get_metadata_by_affect(identifier.command_identifier):
            metadatum = await interceptor.from_buffer(command, metadata)
            await metadatum.intercept(command)

        if not self.has_binary(parameter.data_type):
            msg = "Expected a fully qualified parameter identifier containing a 'Binary'."
            raise BinaryUploadFailed(msg)

        binary = BinaryTransfer.new(size=request.binary_size, chunks=request.chunk_count)
        self._binaries[binary.binary_transfer_uuid] = binary

        return CreateBinaryResponse(
            binary_transfer_uuid=binary.binary_transfer_uuid,
            lifetime_of_binary=Duration.from_total_seconds(binary.lifetime.total_seconds),
        )

    async def upload_chunk(self, request: UploadChunkRequest) -> UploadChunkResponse:
        """
        Upload a chunk of data as part of a binary transfer session.

        Args:
          request: The client's requests to upload an individual chunk.

        Returns:
          Information to acknowledge the successful upload of the chunk.

        Raises:
          InvalidBinaryTransferUUID: If the given identifier is invalid
            or not recognized.
          BinaryUploadFailed: If an error occurs during the upload.
        """

        try:
            binary = self.get_binary_by_uuid(request.binary_transfer_uuid)
            binary.set_chunk(request.chunk_index, request.payload)
        except ValueError as error:
            raise BinaryUploadFailed(str(error)) from None

        return UploadChunkResponse(
            binary_transfer_uuid=request.binary_transfer_uuid,
            chunk_index=request.chunk_index,
            lifetime_of_binary=Duration.from_total_seconds(binary.lifetime.total_seconds),
        )

    async def get_binary_info(self, request: GetBinaryInfoRequest) -> GetBinaryInfoResponse:
        """
        Retrieve information about a specific binary transfer session.

        Args:
          request: The client's request containing the binary transfer
            uuid for which to get the details.

        Returns:
          Information about the binary transfer.

        Raises:
          InvalidBinaryTransferUUID: If the given identifier is invalid
            or not recognized.
        """

        try:
            binary = self.get_binary_by_uuid(request.binary_transfer_uuid)
        except BinaryTransferError as error:
            raise error from None

        return GetBinaryInfoResponse(
            binary_size=binary.size,
            lifetime_of_binary=Duration.from_total_seconds(binary.lifetime.total_seconds),
        )

    async def download_chunk(self, request: DownloadChunkRequest) -> DownloadChunkResponse:
        """
        Download a chunk of data as part of a binary transfer session.

        Args:
          request: The client's request to downlaod an individual chunk.

        Returns:
          The data of the individually requested chunk.

        Raises:
          InvalidBinaryTransferUUID: If the given identifier is invalid
            or not recognized.
          BinaryDownloadFailed: If an error occurs during the upload.
        """

        try:
            binary = self.get_binary_by_uuid(request.binary_transfer_uuid)
            payload = binary.get_chunk(request.offset, request.length)
        except ValueError as error:
            raise BinaryDownloadFailed(str(error)) from None
        except BinaryTransferError as error:
            raise error from None

        return DownloadChunkResponse(
            binary_transfer_uuid=request.binary_transfer_uuid,
            offset=request.offset,
            payload=payload,
            lifetime_of_binary=Duration.from_total_seconds(binary.lifetime.total_seconds),
        )

    async def delete_binary(self, request: DeleteBinaryRequest) -> DeleteBinaryResponse:
        """
        Delete all data from a binary transfer session.

        Args:
          request: The client's request containing the binary transfer
            uuid for which to delete the details.

        Returns:
          Confirm the deletion of a binary transfer session.

        Raises:
          InvalidBinaryTransferUUID: If the given identifier is invalid
            or not recognized.
        """

        try:
            binary = self.get_binary_by_uuid(request.binary_transfer_uuid)
        except BinaryTransferError as error:
            raise error from None

        self._binaries.pop(binary.binary_transfer_uuid)
        return DeleteBinaryResponse()

    def get_binary_by_uuid(self, binary_transfer_uuid: str) -> BinaryTransfer:
        """
        Get a binary by its unique identifier (UUID).

        Args:
          binary_transfer_uuid: A unique identifier (UUID) for the binary
            transfer session from which to get the large binary.

        Returns:
          The binary transfer associated with the specified identifier.

        Raises:
          InvalidBinaryTransferUUID: If the given identifier is invalid
            or not recognized.
        """

        try:
            uuid.UUID(binary_transfer_uuid, version=4)
        except ValueError:
            msg = f"Expected 'binary_transfer_uuid' with format UUID, received '{binary_transfer_uuid}'."
            raise InvalidBinaryTransferUUID(msg) from None

        if binary_transfer_uuid not in self._binaries:
            msg = f"Requested unknown Binary with 'binary_transfer_uuid' of '{binary_transfer_uuid}'."
            raise InvalidBinaryTransferUUID(msg)

        binary = self._binaries[binary_transfer_uuid]

        if binary.lifetime.total_seconds <= 0:
            del self._binaries[binary_transfer_uuid]
            msg = f"Requested Binary '{binary_transfer_uuid}' with exceeded lifetime."
            raise InvalidBinaryTransferUUID(msg)

        return binary

    @classmethod
    def has_binary(cls, data_type: type[DataType]) -> bool:
        """
        Check whether the given data type accepts binary data.

        Args:
          data_type: The data type to check.

        Returns:
          Whether the given data type contains a binary value.
        """

        if issubclass(data_type, Binary):
            return True
        if issubclass(data_type, (List, Constrained, Custom)):
            return cls.has_binary(data_type.data_type)
        if issubclass(data_type, Structure):
            return any(cls.has_binary(element.data_type) for element in data_type.elements.values())

        return False

    async def _create_binary(
        self, request: CreateBinaryRequest, context: grpc.aio.ServicerContext
    ) -> CreateBinaryResponse:
        """
        RPC handler to create a new binary transfer session.

        Args:
          request: The client's request to create a new binary.
          context: The gRPC call context.

        Returns:
          Information about the newly created binary.
        """

        try:
            metadata: dict[str, bytes] = {
                key: value
                for key, value in context.invocation_metadata() or ()
                if key.startswith("sila-") and key.endswith("-bin") and isinstance(value, bytes)
            }

            return await self.create_binary(request, metadata)
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    async def _upload_chunk(
        self, request_iterator: collections.abc.AsyncIterator[UploadChunkRequest], context: grpc.aio.ServicerContext
    ) -> collections.abc.AsyncIterator[UploadChunkResponse]:
        """
        RPC handler to upload chunks of data as part of a binary transfer session.

        Args:
          request_iterator: The client's requests to upload individual
            chunks.
          context: The gRPC call context.

        Returns:
          Information to acknowledge the successful upload of a specific
          chunk.
        """

        try:
            async for request in request_iterator:
                yield await self.upload_chunk(request)
        except BinaryTransferError as error:
            raise await error.to_rpc_error(context) from None

    async def _get_binary_info(
        self, request: GetBinaryInfoRequest, context: grpc.aio.ServicerContext
    ) -> GetBinaryInfoResponse:
        """
        RPC handler to retrieve information about a specific binary transfer session.

        Args:
          request: The client's request containing the binary transfer
            uuid for which to get the details.
          context: The gRPC call context.

        Returns:
          Information about the binary transfer.
        """

        try:
            return await self.get_binary_info(request)
        except BinaryTransferError as error:
            raise await error.to_rpc_error(context) from None

    async def _download_chunk(
        self, request_iterator: collections.abc.AsyncIterator[DownloadChunkRequest], context: grpc.aio.ServicerContext
    ) -> collections.abc.AsyncIterator[DownloadChunkResponse]:
        """
        RPC handler to download chunks of data as part of a binary transfer session.

        Args:
          request_iterator: The client's requests to downlaod individual
            chunks.
          context: The gRPC call context.

        Returns:
          The data of the individually requested chunk.
        """

        try:
            async for request in request_iterator:
                yield await self.download_chunk(request)
        except BinaryTransferError as error:
            raise await error.to_rpc_error(context) from None

    async def _delete_binary(
        self, request: DeleteBinaryRequest, context: grpc.aio.ServicerContext
    ) -> DeleteBinaryResponse:
        """
        RPC handler to delete all data from a binary transfer session.

        Args:
          request: The client's request containing the binary transfer
            uuid for which to delete the details.
          context: The gRPC call context.

        Returns:
          Confirm the deletion of a binary transfer session.
        """

        try:
            return await self.delete_binary(request)
        except BinaryTransferError as error:
            raise await error.to_rpc_error(context) from None
