import dataclasses
import time
import uuid

import typing_extensions as typing

from ..data_types import Duration


@dataclasses.dataclass
class BinaryTransfer:
    """
    Storage and retrieval of chunks for binary data transfers.

    Attributes:
      max_chunk_size: The maximum size of each chunk in bytes.
      binary_transfer_uuid: A unique identifier for the binary
        transfer.
      created_at: The timestamp when the binary transfer was created.
      valid_for: Fractional seconds for how long the binary transfer
        is valid.
      size: The total size of the binary data in bytes.
      chunks: A list of chunks containing the binary data.
    """

    max_chunk_size: typing.ClassVar[int] = 2**21

    binary_transfer_uuid: str = dataclasses.field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = dataclasses.field(default_factory=time.monotonic)
    valid_for: float = dataclasses.field(default=60)
    size: int = 0
    chunks: list[typing.Optional[bytes]] = dataclasses.field(default_factory=list)

    @classmethod
    def new(cls, size: int, chunks: int) -> typing.Self:
        """
        Reserve space for a new binary transfer.

        Args:
          size: The amount of bytes to reserve.
          chunks: The number of expected chunks.

        Returns:
          An instance of a new binary transfer.
        """

        return cls(size=size, chunks=[None] * chunks)

    @classmethod
    def from_buffer(cls, buffer: bytes) -> typing.Self:
        """
        Create a new binary transfer with the given buffer.

        Args:
          buffer: The actual bytes data for this binary transfer.

        Returns:
          An instance of a new binary transfer.
        """

        size = len(buffer)

        return cls(
            size=size,
            chunks=[buffer[i : i + cls.max_chunk_size] for i in range(0, size, cls.max_chunk_size)],
        )

    @property
    def is_completed(self) -> bool:
        """Whether the binary transfer has been completed or not."""

        return not any(chunk is None for chunk in self.chunks)

    @property
    def buffer(self) -> bytes:
        """The complete buffer of the binary transfer."""

        return b"".join(chunk or b"" for chunk in self.chunks)

    @property
    def lifetime(self) -> Duration:
        """The duration in which this binary transfer is valid."""

        return Duration.from_total_seconds(self.created_at + self.valid_for - time.monotonic())

    def get_chunk(self, offset: int, length: int) -> bytes:
        """
        Retrieve a specific chunk of binary data.

        Args:
          offset: The starting byte position within the binary data from
            which to begin retrieving the chunk.
          length: The number of bytes to retrieve starting from the
            offset position.

        Returns:
          The requested chunk of binary data.
        """

        if length > self.max_chunk_size:
            msg = (
                f"Expected length of chunk with offset '{offset}' to not exceed the "
                f"maximum size of 2 MiB, received {length} bytes."
            )
            raise ValueError(msg)

        if offset > self.size:
            msg = f"Expected offset to not exceed the binary's size of {self.size} bytes, received {offset} bytes."
            raise ValueError(msg)

        if offset + length > self.size:
            msg = (
                f"Expected length of chunk with offset '{offset}' to not exceed the "
                f"binary's size of {self.size} bytes, received {length} bytes."
            )
            raise ValueError(msg)

        return self.buffer[offset : offset + length]

    def set_chunk(self, index: int, payload: bytes) -> None:
        """
        Set a specific chunk of binary data.

        Args:
          index: The index of the chunk within the binary transfer.
          payload: The actual binary data chunk being set.
        """

        if self.is_completed:
            msg = f"Received chunk with index '{index}' for already completed binary transfer."
            raise ValueError(msg)

        if len(payload) > self.max_chunk_size:
            msg = f"Expected chunk '{index}' to not exceed the maximum size of 2 MiB, received {len(payload)} bytes."
            raise ValueError(msg)

        if index >= len(self.chunks):
            msg = f"Expected chunks up to index '{len(self.chunks) - 1}', received '{index}'."
            raise ValueError(msg)

        if self.chunks[index] is not None:
            msg = f"Received chunk with index '{index}' for already received chunk."
            raise ValueError(msg)

        self.chunks[index] = payload

        current_size = sum(len(chunk) for chunk in self.chunks if chunk is not None)
        if current_size > self.size:
            msg = (
                f"Expected a total size of {self.size} bytes, received "
                f"already {current_size} bytes with chunk '{index}'."
            )
            raise ValueError(msg)
