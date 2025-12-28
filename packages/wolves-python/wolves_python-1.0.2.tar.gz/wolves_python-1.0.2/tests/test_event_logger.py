from __future__ import annotations

import asyncio
import threading
import time

from wolves_python.event_logger import EventLogger
from wolves_python.runtime import AsyncRuntime
from wolves_python.types import WolvesEvent, WolvesUser


class FakeNetwork:
    def __init__(self, *, fail_times: int = 0) -> None:
        self._lock = threading.Lock()
        self._fail_times = fail_times
        self.calls: list[list[str]] = []

    def set_fail_times(self, fail_times: int) -> None:
        with self._lock:
            self._fail_times = fail_times

    async def send_events(self, events: list[WolvesEvent]) -> None:
        await asyncio.sleep(0)
        with self._lock:
            self.calls.append([e.event_name for e in events])
            if self._fail_times > 0:
                self._fail_times -= 1
                raise RuntimeError("boom")


def _wait_until(predicate, *, timeout_s: float = 1.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    assert predicate()


def test_event_logger_flush_success() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        logger.enqueue(WolvesEvent(event_name="e1", user=WolvesUser(user_id="u"), time_ms=0))
        logger.flush().wait(timeout=2)
        _wait_until(lambda: len(network.calls) == 1)
        assert network.calls[0] == ["e1"]
        assert logger._last_flush_success is True  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_overflow_triggers_flush() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, max_queue_size=2, flush_interval_s=999)
    try:
        logger.enqueue(WolvesEvent(event_name="e1", user=None, time_ms=0))
        logger.enqueue(WolvesEvent(event_name="e2", user=None, time_ms=0))
        _wait_until(lambda: len(network.calls) == 1)
        assert network.calls[0] == ["e1", "e2"]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_requeues_and_trims_on_failure() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork(fail_times=1)
    logger = EventLogger(network, runtime, max_queue_size=2, flush_interval_s=999)
    try:
        async def seed_queue() -> None:
            logger._queue.extend(  # type: ignore[attr-defined]
                [
                    WolvesEvent(event_name="e1", user=None, time_ms=0),
                    WolvesEvent(event_name="e2", user=None, time_ms=0),
                    WolvesEvent(event_name="e3", user=None, time_ms=0),
                ]
            )

        runtime.submit(seed_queue()).wait(timeout=2)

        logger.flush().wait(timeout=2)
        _wait_until(lambda: len(network.calls) >= 1, timeout_s=2.0)
        assert network.calls[0] == ["e1", "e2", "e3"]
        assert logger._last_flush_success is False  # type: ignore[attr-defined]

        logger.flush().wait(timeout=2)
        _wait_until(lambda: len(network.calls) >= 2, timeout_s=2.0)
        assert network.calls[1] == ["e2", "e3"]
        assert logger._last_flush_success is True  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_periodic_flushes() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=0.05)
    try:
        logger.enqueue(WolvesEvent(event_name="e", user=None, time_ms=0))
        _wait_until(lambda: len(network.calls) >= 1, timeout_s=2.0)
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_start_and_stop_are_idempotent() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        runtime.submit(logger._start()).wait(timeout=2)  # type: ignore[attr-defined]
        logger.stop().wait(timeout=2)
        logger.stop().wait(timeout=2)
    finally:
        runtime.stop()


def test_event_logger_enqueue_after_stop_is_noop() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        logger.stop().wait(timeout=2)
        logger.enqueue(WolvesEvent(event_name="e", user=None, time_ms=0))
        time.sleep(0.05)
        assert network.calls == []
    finally:
        runtime.stop()


def test_event_logger_flush_noop_when_empty() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        logger.flush().wait(timeout=2)
        assert logger._last_flush_success is None  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_start_with_preexisting_lock_skips_lock_init_branch() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        async def reconfigure() -> None:
            if logger._periodic_task is not None:  # type: ignore[attr-defined]
                logger._periodic_task.cancel()  # type: ignore[attr-defined]
                try:
                    await logger._periodic_task  # type: ignore[attr-defined]
                except asyncio.CancelledError:
                    pass
                logger._periodic_task = None  # type: ignore[attr-defined]
            logger._flush_lock = asyncio.Lock()  # type: ignore[attr-defined]
            await logger._start()  # type: ignore[attr-defined]

        runtime.submit(reconfigure()).wait(timeout=2)
        assert logger._periodic_task is not None  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_flush_creates_lock_when_missing() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        async def seed_and_clear_lock() -> None:
            logger._flush_lock = None  # type: ignore[attr-defined]
            logger._queue.append(WolvesEvent(event_name="e", user=None, time_ms=0))  # type: ignore[attr-defined]

        runtime.submit(seed_and_clear_lock()).wait(timeout=2)
        logger.flush().wait(timeout=2)
        _wait_until(lambda: len(network.calls) == 1)
        assert logger._flush_lock is not None  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_failure_without_trim_covers_branch() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork(fail_times=1)
    logger = EventLogger(network, runtime, max_queue_size=10, flush_interval_s=999)
    try:
        logger.enqueue(WolvesEvent(event_name="e", user=None, time_ms=0))
        logger.flush().wait(timeout=2)
        _wait_until(lambda: len(network.calls) == 1)
        assert logger._last_flush_success is False  # type: ignore[attr-defined]
    finally:
        logger.stop().wait(timeout=2)
        runtime.stop()


def test_event_logger_stop_when_periodic_task_missing_covers_branch() -> None:
    runtime = AsyncRuntime()
    network = FakeNetwork()
    logger = EventLogger(network, runtime, flush_interval_s=999)
    try:
        async def clear_periodic() -> None:
            if logger._periodic_task is not None:  # type: ignore[attr-defined]
                logger._periodic_task.cancel()  # type: ignore[attr-defined]
                try:
                    await logger._periodic_task  # type: ignore[attr-defined]
                except asyncio.CancelledError:
                    pass
                logger._periodic_task = None  # type: ignore[attr-defined]

        runtime.submit(clear_periodic()).wait(timeout=2)
        logger.stop().wait(timeout=2)
    finally:
        runtime.stop()
