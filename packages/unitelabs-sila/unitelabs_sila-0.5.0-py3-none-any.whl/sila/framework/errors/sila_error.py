import base64

import grpc
import grpc.aio
import typing_extensions as typing

from ..protobuf import DecodeError, EncodeError, Message, Reader, WireType, Writer


class SiLAError(Exception, Message):
    """
    Any error that can occur during communication via SiLA.

    Args:
      message: An error message providing additional context or
        details about the error and how to resolve it.
    """

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)

    @property
    def message(self) -> str:
        """An explanation of why the error occurred."""

        return self.args[0]

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> "SiLAError":
        from .defined_execution_error import DefinedExecutionError
        from .framework_error import FrameworkError
        from .undefined_execution_error import UndefinedExecutionError
        from .validation_error import ValidationError

        reader = reader if isinstance(reader, Reader) else Reader(reader)

        message = None
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            tag = reader.read_uint32()
            field_number = tag >> 3

            if field_number == 1:
                reader.expect_type(tag, WireType.LEN)
                message = ValidationError.decode(reader, reader.read_uint32())
            elif field_number == 2:
                reader.expect_type(tag, WireType.LEN)
                message = DefinedExecutionError.decode(reader, reader.read_uint32())
            elif field_number == 3:
                reader.expect_type(tag, WireType.LEN)
                message = UndefinedExecutionError.decode(reader, reader.read_uint32())
            elif field_number == 4:
                reader.expect_type(tag, WireType.LEN)
                message = FrameworkError.decode(reader, reader.read_uint32())
            else:
                reader.skip_type(tag & 7)

        if message is None:
            msg = "Expected at least one valid error type."
            raise DecodeError(msg, reader.cur)

        return message

    @typing.override
    def encode(self, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        msg = "Can only encode subclasses of SiLA error."
        raise EncodeError(msg)

    async def to_rpc_error(self, context: grpc.aio.ServicerContext) -> typing.Self:
        """
        Abort the grpc handler and inform the client about the error.

        Args:
          context: The gRPC call context.

        Returns:
          The Error instance, allowing for method chaining.
        """

        message = self.encode()
        details = base64.standard_b64encode(message).decode("ascii")
        await context.abort(code=grpc.StatusCode.ABORTED, details=details)

        return self

    async def from_rpc_error(error: grpc.RpcError) -> typing.Self:
        """
        Create a SiLA error from a gRPC error.

        Args:
          error: The gRPC error.

        Returns:
          The Error instance, allowing for method chaining.
        """

        from .connection_error import SiLAConnectionError

        if error.code() == grpc.StatusCode.ABORTED:
            details = base64.standard_b64decode(error.details().encode("ascii"))
            return SiLAError.decode(details)

        msg = f"{error.code().name}: {error.details()}"
        return SiLAConnectionError(msg)

    def __str__(self) -> str:
        return self.message

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SiLAError):
            return NotImplemented

        return issubclass(self.__class__, other.__class__) and self.args == other.args

    __hash__ = None
