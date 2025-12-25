import dataclasses
import uuid

import typing_extensions as typing

from ..binary_transfer import (
    BinaryTransferError,
    CreateBinaryResponse,
    DeleteBinaryResponse,
    DownloadChunkResponse,
    GetBinaryInfoResponse,
    UploadChunkResponse,
)
from ..errors import SiLAError
from ..protobuf import Message, Reader, WireType, Writer
from .command_confirmation_response import CommandConfirmationResponse
from .command_execution_response import CommandExecutionResponse
from .metadata_response import MetadataResponse
from .observable_command_response import ObservableCommandResponse
from .property_response import PropertyResponse
from .unobservable_command_response import UnobservableCommandResponse


@dataclasses.dataclass
class ServerMessage(Message):
    """
    Message sent from server to client through the cloud stream.

    Attributes:
      request_uuid: Unique ID used to map responses to requests.
    """

    request_uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    unobservable_command_response: typing.Optional[UnobservableCommandResponse] = None
    observable_command_confirmation: typing.Optional[CommandConfirmationResponse] = None
    observable_command_execution_info: typing.Optional[CommandExecutionResponse] = None
    observable_command_intermediate_response: typing.Optional[ObservableCommandResponse] = None
    observable_command_response: typing.Optional[ObservableCommandResponse] = None
    get_fcp_affected_by_metadata_response: typing.Optional[MetadataResponse] = None
    unobservable_property_value: typing.Optional[PropertyResponse] = None
    observable_property_value: typing.Optional[PropertyResponse] = None
    create_binary_response: typing.Optional[CreateBinaryResponse] = None
    upload_chunk_response: typing.Optional[UploadChunkResponse] = None
    delete_binary_response: typing.Optional[DeleteBinaryResponse] = None
    get_binary_info_response: typing.Optional[GetBinaryInfoResponse] = None
    download_chunk_response: typing.Optional[DownloadChunkResponse] = None
    binary_transfer_error: typing.Optional[BinaryTransferError] = None
    command_error: typing.Optional[SiLAError] = None
    property_error: typing.Optional[SiLAError] = None

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = cls(request_uuid="")
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                message.request_uuid = reader.read_string()
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message.unobservable_command_response = UnobservableCommandResponse.decode(reader, reader.read_uint32())
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_confirmation = CommandConfirmationResponse.decode(
                    reader, reader.read_uint32()
                )
            elif field_number == 4:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_execution_info = CommandExecutionResponse.decode(
                    reader, reader.read_uint32()
                )
            elif field_number == 5:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_intermediate_response = ObservableCommandResponse.decode(
                    reader, reader.read_uint32()
                )
            elif field_number == 6:
                reader.expect_type(tag, WireType.LEN)
                message.observable_command_response = ObservableCommandResponse.decode(reader, reader.read_uint32())
            elif field_number == 7:
                reader.expect_type(tag, WireType.LEN)
                message.get_fcp_affected_by_metadata_response = MetadataResponse.decode(reader, reader.read_uint32())
            elif field_number == 8:
                reader.expect_type(tag, WireType.LEN)
                message.unobservable_property_value = PropertyResponse.decode(reader, reader.read_uint32())
            elif field_number == 9:
                reader.expect_type(tag, WireType.LEN)
                message.observable_property_value = PropertyResponse.decode(reader, reader.read_uint32())
            elif field_number == 10:
                reader.expect_type(tag, WireType.LEN)
                message.create_binary_response = CreateBinaryResponse.decode(reader, reader.read_uint32())
            elif field_number == 11:
                reader.expect_type(tag, WireType.LEN)
                message.upload_chunk_response = UploadChunkResponse.decode(reader, reader.read_uint32())
            elif field_number == 12:
                reader.expect_type(tag, WireType.LEN)
                message.delete_binary_response = DeleteBinaryResponse.decode(reader, reader.read_uint32())
            elif field_number == 13:
                reader.expect_type(tag, WireType.LEN)
                message.get_binary_info_response = GetBinaryInfoResponse.decode(reader, reader.read_uint32())
            elif field_number == 14:
                reader.expect_type(tag, WireType.LEN)
                message.download_chunk_response = DownloadChunkResponse.decode(reader, reader.read_uint32())
            elif field_number == 15:
                reader.expect_type(tag, WireType.LEN)
                message.binary_transfer_error = BinaryTransferError.decode(reader, reader.read_uint32())
            elif field_number == 16:
                reader.expect_type(tag, WireType.LEN)
                message.command_error = SiLAError.decode(reader, reader.read_uint32())
            elif field_number == 17:
                reader.expect_type(tag, WireType.LEN)
                message.property_error = SiLAError.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        if self.request_uuid:
            writer.write_uint32(10).write_string(self.request_uuid)

        if self.unobservable_command_response is not None:
            self.unobservable_command_response.encode(writer, 2)

        if self.observable_command_confirmation is not None:
            self.observable_command_confirmation.encode(writer, 3)

        if self.observable_command_execution_info is not None:
            self.observable_command_execution_info.encode(writer, 4)

        if self.observable_command_intermediate_response is not None:
            self.observable_command_intermediate_response.encode(writer, 5)

        if self.observable_command_response is not None:
            self.observable_command_response.encode(writer, 6)

        if self.get_fcp_affected_by_metadata_response is not None:
            self.get_fcp_affected_by_metadata_response.encode(writer, 7)

        if self.unobservable_property_value is not None:
            self.unobservable_property_value.encode(writer, 8)

        if self.observable_property_value is not None:
            self.observable_property_value.encode(writer, 9)

        if self.create_binary_response is not None:
            self.create_binary_response.encode(writer, 10)

        if self.upload_chunk_response is not None:
            self.upload_chunk_response.encode(writer, 11)

        if self.delete_binary_response is not None:
            self.delete_binary_response.encode(writer, 12)

        if self.get_binary_info_response is not None:
            self.get_binary_info_response.encode(writer, 13)

        if self.download_chunk_response is not None:
            self.download_chunk_response.encode(writer, 14)

        if self.binary_transfer_error is not None:
            self.binary_transfer_error.encode(writer, 15)

        if self.command_error is not None:
            self.command_error.encode(writer, 16)

        if self.property_error is not None:
            self.property_error.encode(writer, 17)

        if number:
            writer.ldelim()

        return writer.finish()
