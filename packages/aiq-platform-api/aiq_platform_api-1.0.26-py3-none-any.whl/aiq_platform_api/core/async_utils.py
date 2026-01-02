from typing import AsyncIterable, AsyncIterator, Optional, TypeVar

T = TypeVar("T")


async def async_islice(iterable: AsyncIterable[T], start: int, stop: Optional[int]) -> AsyncIterator[T]:
    """Async equivalent of itertools.islice for sequential iteration."""
    index = 0
    async for item in iterable:
        if index >= start:
            if stop is not None and index >= stop:
                break
            yield item
        index += 1


async def async_take(iterable: AsyncIterable[T], limit: Optional[int]) -> AsyncIterator[T]:
    """Yield up to limit items from an async iterable."""
    if limit is None:
        async for item in iterable:
            yield item
        return

    async for item in async_islice(iterable, 0, limit):
        yield item
