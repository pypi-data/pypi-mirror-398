import asyncio
import collections.abc

import typing_extensions as typing

T = typing.TypeVar("T")


class QueueShutDown(Exception):
    """Raised when putting on to or getting from a shut-down Queue."""


class Stream(collections.abc.AsyncIterator[T]):
    """An AsyncIterable you can asynchronously add items to."""

    def __init__(self, maxsize: int = 0):
        self._queue = asyncio.Queue[typing.Optional[T]]()
        self._maxsize = maxsize
        self._closed = False

    @property
    def size(self) -> int:
        """Number of items in the queue."""

        return self._queue.qsize()

    @property
    def full(self) -> bool:
        """Whether there are `maxsize` items in the Stream."""

        if self._maxsize <= 0:
            return False

        return self.size >= self._maxsize

    def next(self, item: T) -> None:
        """
        Manually set the next item.

        Args:
          item: The item to add to the queue.

        Raises:
          QueueShutDown: If the queue has been shut down.
        """

        if self._closed:
            msg = "Cannot push to a closed queue."
            raise QueueShutDown(msg)

        self._put(item)

    def close(self) -> None:
        """Signal that no more items will be added."""

        self._closed = True
        self._put(None)

    async def get(self, timeout: typing.Optional[float] = None) -> T:
        """
        Get the next item from the queue.

        Args:
          timeout: The number of seconds to wait for. Omit to wait
            indefinitely.

        Returns:
          The next item from the queue.

        Raises:
          TimeoutError: If no new item occured within the given timeout.
        """

        try:
            item = await asyncio.wait_for(self._queue.get(), timeout)
            self._queue.task_done()

            if item is None:
                raise TimeoutError

            return item
        except (TimeoutError, asyncio.TimeoutError):
            raise TimeoutError from None

    def __aiter__(self) -> collections.abc.AsyncIterator[T]:
        return self

    async def __anext__(self) -> T:
        try:
            item = await self._queue.get()
            self._queue.task_done()

            if item is None:
                raise StopAsyncIteration

            return item
        except asyncio.CancelledError:
            raise StopAsyncIteration from None

    def _put(self, item: typing.Optional[T]) -> None:
        if item is not None and self.full:
            self._queue._queue.popleft()  # type: ignore

        self._queue.put_nowait(item)
