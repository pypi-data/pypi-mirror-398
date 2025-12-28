from __future__ import annotations

import concurrent.futures

from wolves_python.future import WolvesFuture


def test_wolves_future_result_done_exception() -> None:
    fut: concurrent.futures.Future[int] = concurrent.futures.Future()
    wf = WolvesFuture(fut)

    assert wf.done() is False
    fut.set_result(3)
    assert wf.done() is True
    assert wf.result(timeout=1) == 3

    err_fut: concurrent.futures.Future[int] = concurrent.futures.Future()
    err = RuntimeError("boom")
    err_fut.set_exception(err)
    wf2 = WolvesFuture(err_fut)
    assert isinstance(wf2.exception(timeout=1), RuntimeError)
