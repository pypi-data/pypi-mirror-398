import grpc.aio
import typing_extensions as typing

from .channel_options import ChannelOptions


async def create_channel(
    target: str,
    /,
    tls: bool = True,
    root_certificates: typing.Optional[bytes] = None,
    certificate_chain: typing.Optional[bytes] = None,
    private_key: typing.Optional[bytes] = None,
    options: typing.Optional[ChannelOptions] = None,
    **kwargs,
) -> grpc.aio.Channel:
    """
    Create a channel to the target.

    Args:
      target: The target address to connect to.
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

    if tls:
        credentials = grpc.ssl_channel_credentials(
            root_certificates=root_certificates,
            private_key=private_key,
            certificate_chain=certificate_chain,
        )
        channel = grpc.aio.secure_channel(target, credentials=credentials, options=list(options.items()))
    else:
        channel = grpc.aio.insecure_channel(target, options=list(options.items()))

    return channel
