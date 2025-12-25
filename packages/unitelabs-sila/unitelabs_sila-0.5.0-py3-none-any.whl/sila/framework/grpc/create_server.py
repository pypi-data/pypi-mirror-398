import grpc.aio
import typing_extensions as typing

from .channel_options import ChannelOptions


async def create_server(
    address: str,
    /,
    tls: bool = True,
    require_client_auth: bool = False,
    root_certificates: typing.Optional[bytes] = None,
    certificate_chain: typing.Optional[bytes] = None,
    private_key: typing.Optional[bytes] = None,
    options: typing.Optional[ChannelOptions] = None,
    **kwargs,
) -> tuple[grpc.aio.Server, int]:
    """
    Create a server at the address.

    Args:
      address: The target address to bind to.
      require_client_auth: A boolean indicating whether or not to
        require clients to be authenticated. May only be True if
        root_certificates is not None.
      tls: Whether to run a secure/TLS channel or a plaintext channel
        (i.e. no TLS), defaults to run with TLS encryption.
      root_certificates: The PEM-encoded root certificates as a byte
        string, or None to retrieve them from a default location
        chosen by gRPC runtime.
      certificate_chain: The PEM-encoded certificate chain as a byte
        string to use or None if no certificate chain should be used.
      private_key: The PEM-encoded private key as a byte string, or
        None if no private key should be used.
      options: Additional options for the underlying gRPC connection.

    Returns:
      The grpc channel connected to cloud client endpoint.
    """

    options = ChannelOptions(options or {})

    server = grpc.aio.server()

    if tls:
        credentials = grpc.ssl_server_credentials(
            private_key_certificate_chain_pairs=[(private_key, certificate_chain)]
            if private_key is not None and certificate_chain is not None
            else [],
            root_certificates=root_certificates,
            require_client_auth=require_client_auth,
        )
        port = server.add_secure_port(address, credentials)
    else:
        port = server.add_insecure_port(address)

    return server, port
