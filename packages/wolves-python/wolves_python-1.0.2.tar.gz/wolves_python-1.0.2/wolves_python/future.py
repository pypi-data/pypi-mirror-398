from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


class WolvesFuture(Generic[T]):
    def __init__(self, inner: concurrent.futures.Future[T]) -> None:
        self._inner = inner

    def __await__(self):
        async def _wait() -> T:
            return await asyncio.wrap_future(self._inner)

        return _wait().__await__()

    def wait(self, timeout: Optional[float] = None) -> T:
        return self._inner.result(timeout=timeout)

    def result(self, timeout: Optional[float] = None) -> T:
        return self._inner.result(timeout=timeout)

    def done(self) -> bool:
        return self._inner.done()

    def exception(self, timeout: Optional[float] = None) -> BaseException | None:
        return self._inner.exception(timeout=timeout)
