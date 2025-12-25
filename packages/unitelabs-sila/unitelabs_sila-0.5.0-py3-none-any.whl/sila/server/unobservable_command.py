import dataclasses
import inspect
import logging

import grpc
import grpc.aio
import typing_extensions as typing

from .. import framework
from ..framework import (
    ConversionError,
    DecodeError,
    DefinedExecutionError,
    Feature,
    MetadataIdentifier,
    Native,
    NoMetadataAllowed,
    Server,
    SiLAError,
    UndefinedExecutionError,
    ValidationError,
)


@dataclasses.dataclass
class UnobservableCommand(framework.UnobservableCommand):
    """Any command for which observing the progress of execution is not possible or does not make sense."""

    function: typing.Callable = dataclasses.field(repr=False, default=lambda **_: ...)
    """The implementation which is executed by the RPC handler."""

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    async def execute(self, request: bytes = b"", metadata: typing.Optional[dict[str, bytes]] = None) -> bytes:
        """
        Execute the command.

        Args:
          request: Input parameters passed to the command.
          metadata: Additional metadata sent from client to server.

        Returns:
          The resulting responses of the command execution.

        Raises:
          NoMetadataAllowed: If providing metadata is not allowed.
          InvalidMetadata: If metadata is missing or invalid.
          CommandExecutionNotAccepted: If the server does not allow
            further command executions.
          ValidationError: If command parameters are missing or invalid.
          DefinedExecutionError: If command execution results in a
            defined execution error
          UnefinedExecutionError: If command execution results in an
            undefined execution error.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        try:
            # Metadata
            if (
                metadata
                and self.fully_qualified_identifier.feature_identifier == "org.silastandard/core/SiLAService/v1"
            ):
                msg = "No metadata allowed for the SiLA Service feature."
                raise NoMetadataAllowed(msg)

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
            responses = self.function(**parameters, metadata=parsed_metadata)

            if inspect.isawaitable(responses):
                responses = await responses

            return await self.feature.context.protobuf.encode(
                f"{self.feature.rpc_package}.{self.identifier}_Responses", responses
            )
        except SiLAError as error:
            if isinstance(error, DefinedExecutionError) and error._identifier is None:
                error = error.with_feature(self.feature.fully_qualified_identifier)

            raise error
        except Exception as error:
            self.logger.exception(error)
            raise UndefinedExecutionError(str(error)) from error

    async def execute_rpc_handler(self, request: bytes, context: grpc.aio.ServicerContext) -> bytes:
        """
        Handle the gRPC call to execute the command.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Returns:
          The response payload in protobuf ecoding.
        """

        try:
            metadata: dict[str, bytes] = {
                key: value
                for key, value in context.invocation_metadata() or ()
                if key.startswith("sila-") and key.endswith("-bin") and isinstance(value, bytes)
            }

            return await self.execute(request, metadata)
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=self.identifier + "_Parameters", message=self.parameters, package=feature.rpc_package
        )
        feature.context.protobuf.register_message(
            name=self.identifier + "_Responses", message=self.responses, package=feature.rpc_package
        )
        feature.context.protobuf.register_service(
            feature.identifier,
            {self.identifier: grpc.unary_unary_rpc_method_handler(self.execute_rpc_handler)},
            package=feature.rpc_package,
        )

        return self
