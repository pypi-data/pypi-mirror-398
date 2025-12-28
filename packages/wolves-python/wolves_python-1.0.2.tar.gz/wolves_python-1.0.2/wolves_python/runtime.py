from __future__ import annotations

import asyncio
import concurrent.futures
import threading
from typing import Coroutine, TypeVar

from .future import WolvesFuture

T = TypeVar("T")


class AsyncRuntime:
    def __init__(self) -> None:
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run, name="wolves-python-runtime", daemon=True)
        self._stopped = threading.Event()
        self._thread.start()

    def _run(self) -> None:
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_forever()
        finally:
            self._loop.run_until_complete(self._loop.shutdown_asyncgens())
            self._loop.close()
            self._stopped.set()

    def submit(self, coro: Coroutine[object, object, T]) -> WolvesFuture[T]:
        if self._stopped.is_set():
            raise RuntimeError("AsyncRuntime is stopped")
        fut: concurrent.futures.Future[T] = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return WolvesFuture(fut)

    def stop(self) -> None:
        if self._stopped.is_set():
            return
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)
        self._stopped.set()

