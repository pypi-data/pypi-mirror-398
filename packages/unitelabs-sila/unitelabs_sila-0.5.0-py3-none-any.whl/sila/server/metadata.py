import dataclasses
import inspect

import grpc
import grpc.aio
import typing_extensions as typing

from .. import framework
from ..framework import (
    Constrained,
    DecodeError,
    DefinedExecutionError,
    Element,
    Handler,
    List,
    Message,
    MetadataIdentifier,
    Native,
    Reader,
    String,
    WireType,
    Writer,
)

if typing.TYPE_CHECKING:
    from ..framework import Feature

T = typing.TypeVar("T", bound=Native)


@dataclasses.dataclass
class Metadata(framework.Metadata[T], Message, typing.Generic[T]):
    """Aditional information the server expects to receive from a client."""

    function: typing.ClassVar[typing.Callable] = lambda *args: ...
    """The implementation which is executed by the RPC handler."""

    async def intercept(self, context: Handler) -> dict[MetadataIdentifier, Native]:
        """
        Intercept the current handler execution with this metadata.

        Args:
          context: The target affected by the interception.

        Raises:
          NoMetadataAllowed: If providing metadata is not allowed.
          InvalidMetadata: If metadata is missing or invalid.
          DefinedExecutionError: If execution the metadata's interceptor
            results in a defined execution error
          UnefinedExecutionError: If execution the metadata's interceptor
            results in an undefined execution error.
        """

        assert self.feature is not None

        native = await self.to_native(self.feature.context)

        try:
            response = self.function(native, context)

            if inspect.isawaitable(response):
                response = await response

        except DefinedExecutionError as error:
            error = error.with_feature(self.feature.fully_qualified_identifier)
            raise error

        return {self.fully_qualified_identifier(): native}

    @classmethod
    async def rpc_handler(cls, request: bytes, context: grpc.aio.ServicerContext) -> bytes:  # noqa: ARG003
        """
        Handle the gRPC call to get the list of affected identifiers.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          The response payload in protobuf ecoding.
        """

        return cls.encode()

    @typing.override
    @classmethod
    def add_to_feature(cls, feature: "Feature") -> type[typing.Self]:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=f"Metadata_{cls.identifier}",
            message={
                "key": Element(
                    identifier=cls.identifier,
                    display_name=cls.display_name,
                    description=cls.description,
                    data_type=cls.data_type,
                )
            },
        )

        feature.context.protobuf.register_service(
            feature.identifier,
            {f"Get_FCPAffectedByMetadata_{cls.identifier}": grpc.unary_unary_rpc_method_handler(cls.rpc_handler)},
            package=feature.rpc_package,
        )

        return cls

    @typing.override
    @classmethod
    def decode(cls, reader: typing.Union[Reader, bytes, bytearray], length: typing.Optional[int] = None) -> typing.Self:
        reader = reader if isinstance(reader, Reader) else Reader(reader)

        flag = False
        message = cls()
        end = reader.length if length is None else reader.cursor + length

        while reader.cursor < end:
            pos = reader.cursor
            tag = reader.read_uint32()

            if tag >> 3 == 1:
                reader.expect_type(tag, WireType.LEN)

                try:
                    if issubclass(cls.data_type, List) or (
                        issubclass(cls.data_type, Constrained) and issubclass(cls.data_type.data_type, List)
                    ):
                        if not flag:
                            values = cls.data_type.decode(reader.buffer[pos:end])
                            message.value = values
                            flag = True

                        reader.skip_type(tag & 7)
                    else:
                        message.value = message.value.decode(reader, reader.read_uint32())
                except DecodeError as error:
                    msg = f"Invalid field '{cls.identifier}' in message '{cls.__name__}': {error.message}"
                    raise DecodeError(msg, error.offset, [cls.identifier, *error.path]) from None

            else:
                reader.skip_type(tag & 7)

        return message

    @typing.override
    @classmethod
    def encode(cls, writer: typing.Optional[Writer] = None, number: typing.Optional[int] = None) -> bytes:
        writer = writer or Writer()

        if number:
            writer.write_uint32((number << 3) | 2).fork()

        for affected_call in cls.affects:
            String(affected_call).encode(writer, number or 1)

        if number:
            writer.ldelim()

        return writer.finish()
