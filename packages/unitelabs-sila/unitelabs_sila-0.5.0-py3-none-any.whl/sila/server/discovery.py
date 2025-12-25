import contextlib
import dataclasses
import ipaddress
import logging
import socket
import weakref

import ifaddr
import typing_extensions as typing
import zeroconf.asyncio

if typing.TYPE_CHECKING:
    from .server import Server


@dataclasses.dataclass
class DiscoveryConfig:
    """Configuration to broadcast a server on the network."""

    ip_version: typing.Literal["all", "ipv4", "ipv6"] = "ipv4"
    """The IP version to use for broadcasting."""

    network_interfaces: list[str] = dataclasses.field(default_factory=list)
    """The network interfaces to broadcast on."""


class Discovery:
    """
    Promotes the provided server on the network.

    In order to provide a true zero-configuration experience, this
    implements multicast DNS (mDNS) and DNS-based Service Discovery
    (DNS-SD). It broadcasts the socket address on which the grpc
    server is available, some metadata about the server and
    optionally the server certificate.

    Args:
      server: The server to promote on the network.
      config: Additional options for broadcasting.
    """

    def __init__(self, server: "Server", config: typing.Optional[DiscoveryConfig] = None):
        self._server: "Server" = weakref.proxy(server)
        self._config = config or DiscoveryConfig()

        ip_version = (
            zeroconf.IPVersion.All
            if self._config.ip_version == "all"
            else zeroconf.IPVersion.V4Only
            if self._config.ip_version == "ipv4"
            else zeroconf.IPVersion.V6Only
        )

        interfaces: zeroconf.InterfacesType = zeroconf.InterfaceChoice.Default
        if self._config.network_interfaces:
            interfaces = []
            adapters = ifaddr.get_adapters()
            for interface in self._config.network_interfaces:
                try:
                    ipaddress.ip_address(interface)
                    interfaces.append(interface)
                except ValueError:
                    for adapter in adapters:
                        if adapter.name == interface:
                            ip = next((ip.ip for ip in adapter.ips if isinstance(ip.ip, str)), adapter.index)
                            interfaces.append(ip)
                            break

        self.mdns = zeroconf.asyncio.AsyncZeroconf(ip_version=ip_version, interfaces=interfaces)

    @property
    def logger(self) -> logging.Logger:
        """A python logger instance."""

        return logging.getLogger(__name__)

    async def start(self) -> None:
        """Start broadcasting the service on mDNS."""

        await self._server.wait_for_ready()
        service = Discovery.create_service(self._server)

        await self.mdns.zeroconf.async_wait_for_start()
        await self.mdns.async_register_service(service)
        self.logger.info("Registered service for discovery.")

    async def stop(self) -> None:
        """Stop broadcasting the service on mDNS."""

        await self.mdns.async_unregister_all_services()
        await self.mdns.async_close()
        self.logger.info("Removed service from discovery.")

    @classmethod
    def find_ip_address(cls, address: str) -> str:
        """
        Return a valid ip address for a given hostname or address.

        Args:
          address: A hostname or address, e.g. `localhost` or `0.0.0.0`.

        Returns:
          A valid ip address that represents the given address.
        """
        if address == "0.0.0.0":
            ip_address = "127.0.0.1"
            with contextlib.suppress(OSError):
                ip_address = socket.gethostbyname(socket.gethostname())

            if ip_address == "127.0.0.1":
                connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                connection.settimeout(0)
                with contextlib.suppress(OSError):
                    connection.connect(("8.8.8.8", 80))
                ip_address = next(iter(connection.getsockname()), ip_address)

            return ip_address

        try:
            return ipaddress.ip_address(address).exploded
        except ValueError:
            try:
                return socket.gethostbyname(address)
            except OSError:
                return "127.0.0.1"

    @classmethod
    def create_service(cls, server: "Server") -> zeroconf.asyncio.AsyncServiceInfo:
        """Create zeroconf service info from the given server."""

        properties = {
            "version": server.version.encode("utf-8")[:247],
            "server_name": server.name.encode("utf-8")[:243],
            "description": server.description.encode("utf-8")[:243],
        }

        if server._config.tls:
            certificate = server._config.certificate_chain
            if certificate:
                properties.update({f"ca{i}": line for i, line in enumerate(certificate.splitlines(keepends=False))})

        hostname, _, port = server._address.rpartition(":")

        return zeroconf.asyncio.AsyncServiceInfo(
            type_="_sila._tcp.local.",
            name=f"{server.uuid}._sila._tcp.local.",
            parsed_addresses=[Discovery.find_ip_address(hostname)],
            port=int(port),
            properties=properties,
        )
