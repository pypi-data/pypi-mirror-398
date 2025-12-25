import typing_extensions as typing

if typing.TYPE_CHECKING:
    from ..common import Execution


@typing.runtime_checkable
class BinaryTransferHandler(typing.Protocol):
    """Handle the transfer of large binaries."""

    async def get_binary(self, binary_transfer_uuid: str) -> bytes:
        """
        Retrieve a large binary by its identifier.

        Args:
          binary_transfer_uuid: A unique identifier (UUID) for the binary
            transfer session from which the large binary was retrieved.

        Returns:
          The actual binary data retrieved from the transfer session.
        """
        ...

    async def set_binary(self, value: bytes, execution: typing.Optional["Execution"] = None) -> str:
        """
        Dispatch a large binary through a binary transfer session.

        Args:
          value: The actual binary data being dispatched through the
            binary transfer session.
          execution: The context of the current command execution.

        Returns:
          A unique identifier (UUID) for the binary transfer session to
          which the data was dispatched.
        """
        ...
