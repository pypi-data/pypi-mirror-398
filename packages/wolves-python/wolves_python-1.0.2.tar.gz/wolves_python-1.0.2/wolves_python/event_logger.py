from __future__ import annotations

import asyncio

from .future import WolvesFuture
from .runtime import AsyncRuntime
from .types import WolvesEvent


class EventLogger:
    def __init__(
        self,
        network: object,
        runtime: AsyncRuntime,
        *,
        max_queue_size: int = 100,
        flush_interval_s: float = 10.0,
    ) -> None:
        self._network = network
        self._runtime = runtime
        self._max_queue_size = max_queue_size
        self._flush_interval_s = flush_interval_s

        self._queue: list[WolvesEvent] = []
        self._periodic_task: asyncio.Task[None] | None = None
        self._flush_lock: asyncio.Lock | None = None
        self._stopped = False
        self._last_flush_success: bool | None = None

        self._runtime.submit(self._start())

    def enqueue(self, event: WolvesEvent) -> None:
        self._runtime.submit(self._enqueue(event))

    def flush(self) -> WolvesFuture[None]:
        return self._runtime.submit(self._flush())

    def stop(self) -> WolvesFuture[None]:
        return self._runtime.submit(self._stop())

    async def _start(self) -> None:
        if self._periodic_task is not None:
            return
        if self._flush_lock is None:
            self._flush_lock = asyncio.Lock()
        self._periodic_task = asyncio.create_task(self._periodic_flush())

    async def _periodic_flush(self) -> None:
        while True:
            await asyncio.sleep(self._flush_interval_s)
            await asyncio.shield(self._flush())

    async def _enqueue(self, event: WolvesEvent) -> None:
        if self._stopped:
            return
        self._queue.append(event)
        if len(self._queue) >= self._max_queue_size:
            asyncio.create_task(self._flush())

    async def _flush(self) -> None:
        if self._flush_lock is None:
            self._flush_lock = asyncio.Lock()

        async with self._flush_lock:
            if not self._queue:
                return

            events = list(self._queue)
            self._queue.clear()

            try:
                send_events = getattr(self._network, "send_events")
                await send_events(events)
                self._last_flush_success = True
            except Exception:
                self._last_flush_success = False
                self._queue[:0] = events
                if len(self._queue) > self._max_queue_size:
                    self._queue = self._queue[len(self._queue) - self._max_queue_size :]

    async def _stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True

        if self._periodic_task is not None:
            self._periodic_task.cancel()
            try:
                await self._periodic_task
            except asyncio.CancelledError:
                pass
            self._periodic_task = None

        await self._flush()
