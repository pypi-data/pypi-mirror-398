from __future__ import annotations

import asyncio

from wolves_python.runtime import AsyncRuntime


def test_runtime_submit_and_wait() -> None:
    runtime = AsyncRuntime()
    try:
        async def work() -> int:
            return 123

        fut = runtime.submit(work())
        assert fut.wait(timeout=2) == 123
    finally:
        runtime.stop()


def test_runtime_stop_rejects_submit() -> None:
    runtime = AsyncRuntime()
    runtime.stop()

    async def work() -> int:
        return 1

    try:
        coro = work()
        try:
            runtime.submit(coro)
        finally:
            coro.close()
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_runtime_future_is_awaitable() -> None:
    runtime = AsyncRuntime()
    try:
        async def main() -> int:
            async def work() -> int:
                return 7

            fut = runtime.submit(work())
            return await fut

        assert asyncio.run(main()) == 7
    finally:
        runtime.stop()


def test_runtime_stop_is_idempotent() -> None:
    runtime = AsyncRuntime()
    runtime.stop()
    runtime.stop()
