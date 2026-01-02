"""
Small patch to asyncio, which would include a default name for every
process asyncio starts, different normal async functions.
"""

import asyncio
import itertools
import threading
from contextvars import ContextVar

_lock = threading.Lock()
_counter = itertools.count(1)

_IN_GATHER: ContextVar[bool] = ContextVar("_IN_GATHER", default=False)

_ORIG_tasks_gather = None
_ORIG_base_create_task = None


def _make_name(prefix: str) -> str:
    return f"{prefix}-{next(_counter)}"


def patch_asyncio_proc_naming(prefix: str = "Proc") -> None:
    """
    Rename ONLY tasks created by asyncio.gather(...) to Proc-{n}, if they were unnamed.

    Covers:
      - await asyncio.gather(*(coro() for ...))   -> renamed (because gather creates Tasks)
      - await asyncio.gather(*tasks)             -> can optionally rename Task-* passed in (see below)
    Does NOT rename:
      - plain `await coro()`
      - asyncio.create_task(coro()) outside gather
    """
    global _ORIG_tasks_gather, _ORIG_base_create_task

    with _lock:
        if _ORIG_tasks_gather is not None:
            return  # already patched

        import asyncio.tasks as tasks
        from asyncio.base_events import BaseEventLoop

        # 1) Patch the REAL gather implementation
        _ORIG_tasks_gather = tasks.gather

        def gather_patched(*aws, **kwargs):
            token = _IN_GATHER.set(True)
            try:
                # Optional: rename already-created Tasks passed into gather
                # (won't affect your "coro list" scenario, but helps other cases)
                for aw in aws:
                    if isinstance(aw, asyncio.Task):
                        try:
                            nm = aw.get_name()
                            if nm.startswith("Task-"):
                                aw.set_name(_make_name(prefix))
                        except Exception:
                            pass

                return _ORIG_tasks_gather(*aws, **kwargs)
            finally:
                _IN_GATHER.reset(token)

        tasks.gather = gather_patched  # type: ignore[assignment]
        asyncio.gather = tasks.gather  # keep alias in sync

        # 2) Patch BaseEventLoop.create_task (where gather creates Tasks from coroutines)
        _ORIG_base_create_task = BaseEventLoop.create_task

        def base_create_task_patched(self, coro, *, name=None, context=None):
            # Only name tasks created while gather is building its task set
            if name is None and _IN_GATHER.get():
                name = _make_name(prefix)

            # 3.11+ supports context=; 3.10 may raise TypeError for it
            try:
                return _ORIG_base_create_task(self, coro, name=name, context=context)
            except TypeError:
                return _ORIG_base_create_task(self, coro, name=name)

        BaseEventLoop.create_task = base_create_task_patched  # type: ignore[assignment]


def unpatch_asyncio_proc_naming() -> None:
    global _ORIG_tasks_gather, _ORIG_base_create_task

    with _lock:
        if _ORIG_tasks_gather is None:
            return

        import asyncio.tasks as tasks
        from asyncio.base_events import BaseEventLoop

        tasks.gather = _ORIG_tasks_gather  # type: ignore[assignment]
        asyncio.gather = tasks.gather  # type: ignore[assignment]

        BaseEventLoop.create_task = _ORIG_base_create_task  # type: ignore[assignment]

        _ORIG_tasks_gather = None
        _ORIG_base_create_task = None



