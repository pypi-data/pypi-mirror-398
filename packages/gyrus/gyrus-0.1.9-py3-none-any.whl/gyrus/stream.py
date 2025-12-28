import asyncio
from typing import Any, AsyncIterator


class Stream:
    """A Go-like channel implementation using asyncio.Queue."""

    def __init__(self, maxsize: int = 0):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._closed = False

    async def send(self, value: Any) -> bool:
        """Send a value to the channel (like ch <- value in Go)."""
        if self._closed:
            return False

        await self._queue.put(value)
        return True

    def send_nowait(self, value: Any) -> bool:
        """Non-blocking send."""
        if self._closed:
            return False
        self._queue.put_nowait(value)
        return True

    async def receive(self) -> tuple[Any, bool]:
        """Receive a value from channel (like value, ok := <-ch in Go)."""
        if self._closed and self._queue.empty():
            return None, False
        try:
            value = await self._queue.get()
            return value, True
        except asyncio.CancelledError:
            return None, False

    def close(self):
        """Close the channel."""
        self._closed = True

    @property
    def is_closed(self) -> bool:
        return self._closed and self._queue.empty()

    async def __aiter__(self) -> AsyncIterator[Any]:
        """Iterate over channel values (like for value := range ch in Go)."""
        while True:
            if self._closed and self._queue.empty():
                break

            try:
                yield await asyncio.wait_for(self._queue.get(), timeout=0.1)
            except asyncio.TimeoutError:
                if self._closed:
                    break
                continue
