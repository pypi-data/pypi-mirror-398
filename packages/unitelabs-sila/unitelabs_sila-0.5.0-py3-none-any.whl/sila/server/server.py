import dataclasses
import functools
import logging
import uuid

import grpc.aio
import typing_extensions as typing

from sila import framework

from ..framework import (
    ChannelOptions,
    VersionLevel,
    check_display_name,
    check_identifier,
    check_url,
    check_uuid,
    check_version,
    create_server,
)
from .binary_transfer_handler import ServerBinaryTransferHandler


@dataclasses.dataclass
class ServerConfig:
    """Configuration to run a SiLA 2 server."""

    hostname: str = "0.0.0.0"
    """The target hostname to bind to. Defaults to `0.0.0.0`."""

    port: int = 0
    """
    The target port to bind to. If set to `0` an available port is
    chosen at runtime. Defaults to `0`.
    """

    tls: bool = False
    """
    Whether to run a secure/TLS server or a plaintext server (i.e. no
    TLS), defaults to run with TLS encryption.
    """

    require_client_auth: bool = False
    """
    A boolean indicating whether or not to require clients to be
    authenticated. May only be True if root_certificates is not None.
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

    options: ChannelOptions = dataclasses.field(default_factory=ChannelOptions)
    """
    Additional options for the underlying gRPC connection.
    """

    uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    """
    Uniquely identifies the SiLA server. Needs to remain the same even after restarting the server.
    Follows the textual representation of UUIDs, e.g. "082bc5dc-18ae-4e17-b028-6115bbc6d21e".
    """

    name: str = "SiLA Server"
    """
    Human readable name of the SiLA server. This value is configurable during runtime via the SiLA
    Service feature's `set_server_name` command. Must not exceed 255 characters.
    """

    type: str = "ExampleServer"
    """
    Human readable identifier of the SiLA server used to describe the entity the server represents.
    Starts with a capital letter, continued by letters and digits up to a maximum of 255 characters.
    """

    description: str = ""
    """Describes the use and purpose of the SiLA Server."""

    version: str = "0.1.0"
    """
    The version of the SiLA server following the Semantic Versioning specification with pre-release
    identifiers separated by underscores, e.g. "3.19.373_mighty_lab_devices".
    """

    vendor_url: str = "https://sila-standard.com"
    """
    URL to the website of the vendor or the website of the product of this SiLA Server. Follows the
    Uniform Resource Locator specification in RFC 1738.
    """


class Server(framework.Server):
    """
    A SiLA 2 compliant gRPC server.

    A SiLA Server can either be a physical laboratory instrument or a software system that offers
    functionalities to clients. These functions are specified and described in Features.
    """

    uuid: str = ""
    """
    The SiLA server UUID is a UUID of a SiLA server. Each SiLA server must generate a UUID once, to uniquely identify
    itself. It needs to remain the same even after the lifetime of a SiLA server has ended.
    """

    type: str = ""
    """
    The SiLA server type is a human readable identifier of the SiLA server used to describe the entity that the SiLA
    server represents. For example, the make and model for a hardware device. A SiLA server type must comply with the
    rules for any identifier and start with an upper-case letter (A-Z) and may be continued by lower and upper-case
    letters (A-Z and a-z) and digits (0-9) up to a maximum of 255 characters in length.
    """

    name: str = ""
    """
    The SiLA server name is a human readable name of the SiLA server. By default this name should be equal to the SiLA
    server type. This property must be configurable via the SiLA service feature's “Set Server Name” command. This
    property has no uniqueness guarantee. A SiLA server name is the display name of a SiLA server (i.e. must comply with
    the rules for any display name, hence be a string of unicode characters of maximum 255 characters in length).
    """

    version: str = "0.1.0"
    """
    The SiLA server version is the version of the SiLA server. A "Major" and a "Minor" version number (e.g. 1.0) must be
    provided, a "Patch" version number may be provided. Optionally, an arbitrary text, separated by an underscore may be
    appended, e.g. “3.19.373_mighty_lab_devices”.
    """

    description: str = ""
    """
    The SiLA server description is the description of the SiLA server. It should include the use and purpose of this
    SiLA server.
    """

    vendor_url: str = ""
    """
    The SiLA server vendor URL is the URL to the website of the vendor or the website of the product of this SiLA
    server. This URL should be accessible at all times. The URL is a Uniform Resource Locator as defined in RFC 1738.
    """

    def __init__(self, config: typing.Optional[typing.Union[dict, ServerConfig]] = None, /):
        super().__init__()

        if isinstance(config, dict):
            import warnings

            warnings.warn(
                "Providing ServerConfig as a dictionary is deprecated and will be removed in a future release. "
                "Please provide a ServerConfig instance instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
            self._config = ServerConfig(**config)
        else:
            self._config = config or ServerConfig()

        self._address = f"{self._config.hostname}:{self._config.port}"
        self._options = self._config.options
        self._server: typing.Optional[grpc.aio.Server] = None
        self._binary_transfer_handler: "ServerBinaryTransferHandler" = ServerBinaryTransferHandler(self)

        self.uuid = check_uuid(self._config.uuid)
        self.type = check_identifier(self._config.type)
        self.name = check_display_name(self._config.name)
        self.version = check_version(self._config.version, required=VersionLevel.MINOR, optional=VersionLevel.LABEL)
        self.description = self._config.description
        self.vendor_url = check_url(self._config.vendor_url)

        from .sila_service import SiLAService

        self.register_feature(SiLAService())

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    @typing.override
    async def _start(self) -> None:
        await super()._start()

        self._server, port = await functools.partial(create_server, **dataclasses.asdict(self._config))(self._address)
        self._address = f"{self._address.rpartition(':')[0]}:{port}"
        self.logger.info(f"{self.__class__.__name__} bound to '{self._address}'.")

        for service, method_handlers in self.protobuf.services.items():
            handlers = grpc.method_handlers_generic_handler(service, method_handlers)
            self._server.add_generic_rpc_handlers((handlers,))

        await self._server.start()

    @typing.override
    async def _stop(self, grace: typing.Optional[float] = None) -> None:
        await super()._stop(grace)

        if self._server is not None:
            await self._server.stop(grace=grace)
