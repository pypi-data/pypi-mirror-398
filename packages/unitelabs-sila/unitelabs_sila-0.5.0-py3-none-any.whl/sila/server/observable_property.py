import collections.abc
import dataclasses
import inspect
import logging

import grpc
import grpc.aio
import typing_extensions as typing

from .. import framework
from ..framework import (
    DefinedExecutionError,
    Element,
    Feature,
    MetadataIdentifier,
    Native,
    Server,
    SiLAError,
    UndefinedExecutionError,
)


@dataclasses.dataclass
class ObservableProperty(framework.ObservableProperty):
    """A property describes certain aspects of a SiLA server that do not require an action on the SiLA server."""

    function: typing.Callable = dataclasses.field(repr=False, default=lambda **_: ...)
    """The implementation which is executed by the RPC handler."""

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    async def subscribe(
        self, metadata: typing.Optional[dict[str, bytes]] = None
    ) -> collections.abc.AsyncIterator[bytes]:
        """
        Subscribe to value changes of the property.

        Args:
          metadata: Additional metadata sent from client to server.

        Yields:
          The current value of the property.

        Raises:
          NoMetadataAllowed: If providing metadata is not allowed.
          InvalidMetadata: If metadata is missing or invalid.
          DefinedExecutionError: If property access results in a defined
            execution error
          UnefinedExecutionError: If property access results in an
            undefined execution error.
        """

        assert self.feature is not None and isinstance(self.feature.context, Server)

        try:
            # Metadata
            parsed_metadata = dict[MetadataIdentifier, Native]()
            for interceptor in self.feature.context.get_metadata_by_affect(self.fully_qualified_identifier):
                metadatum = await interceptor.from_buffer(self, metadata)
                parsed_metadata.update(await metadatum.intercept(self))

            # Execute
            response = self.function(metadata=parsed_metadata)

            if inspect.isasyncgen(response):
                async for value in response:
                    yield await self.feature.context.protobuf.encode(
                        f"{self.feature.rpc_package}.Subscribe_{self.identifier}_Responses", value
                    )

            elif inspect.isgenerator(response):
                for value in response:
                    yield await self.feature.context.protobuf.encode(
                        f"{self.feature.rpc_package}.Subscribe_{self.identifier}_Responses", value
                    )
        except SiLAError as error:
            if isinstance(error, DefinedExecutionError) and error._identifier is None:
                error = error.with_feature(self.feature.fully_qualified_identifier)

            raise error
        except Exception as error:
            self.logger.exception(error)
            raise UndefinedExecutionError(str(error)) from error

    async def subscribe_rpc_handler(
        self,
        request: bytes,  # noqa: ARG002
        context: grpc.aio.ServicerContext,
    ) -> collections.abc.AsyncIterator[bytes]:
        """
        Handle the gRPC call to subscribe to value changes of the property.

        Args:
          request: The request payload in protobuf ecoding.
          context: The gRPC call context.

        Yields:
          The current value of the property.
        """

        try:
            metadata: dict[str, bytes] = {
                key: value
                for key, value in context.invocation_metadata() or ()
                if key.startswith("sila-") and key.endswith("-bin") and isinstance(value, bytes)
            }

            async for value in self.subscribe(metadata):
                yield value
        except SiLAError as error:
            raise await error.to_rpc_error(context) from None

    @typing.override
    def add_to_feature(self, feature: "Feature") -> typing.Self:
        super().add_to_feature(feature)

        feature.context.protobuf.register_message(
            name=f"Subscribe_{self.identifier}_Responses",
            message={
                self.identifier: Element(
                    identifier=self.identifier,
                    display_name=self.display_name,
                    description=self.description,
                    data_type=self.data_type,
                )
            },
            package=feature.rpc_package,
        )
        feature.context.protobuf.register_service(
            feature.identifier,
            {f"Subscribe_{self.identifier}": grpc.unary_stream_rpc_method_handler(self.subscribe_rpc_handler)},
            package=feature.rpc_package,
        )

        return self
