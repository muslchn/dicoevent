"""Celery compatibility layer.

Allows using @shared_task even when Celery isn't installed.
"""

from __future__ import annotations

from importlib import import_module
from functools import update_wrapper
from typing import Any, Callable


def _resolve_celery_shared_task():
    """Load celery.shared_task lazily to keep Celery optional."""

    try:
        celery_module = import_module("celery")
    except ModuleNotFoundError:  # pragma: no cover
        return None
    return getattr(celery_module, "shared_task", None)


class _EagerTask:
    """Fallback task wrapper with sync .delay() behavior."""

    def __init__(self, fn: Callable[..., Any]):
        self.fn = fn
        update_wrapper(self, fn)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def delay(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


def shared_task(*decorator_args: Any, **decorator_kwargs: Any):
    """Return Celery shared_task when available, otherwise sync wrapper."""

    celery_shared_task = _resolve_celery_shared_task()
    if celery_shared_task is not None:
        return celery_shared_task(*decorator_args, **decorator_kwargs)

    # Support both @shared_task and @shared_task(...) signatures.
    if decorator_args and callable(decorator_args[0]) and not decorator_kwargs:
        return _EagerTask(decorator_args[0])

    def _decorator(fn: Callable[..., Any]):
        return _EagerTask(fn)

    return _decorator


def enqueue_task(task: Any, *args: Any, **kwargs: Any) -> Any:
    """Execute task asynchronously when available, otherwise synchronously.

    This keeps call sites type-safe across both Celery and fallback wrappers.
    """

    delay_fn = getattr(task, "delay", None)
    if callable(delay_fn):
        return delay_fn(*args, **kwargs)
    if callable(task):
        return task(*args, **kwargs)
    raise TypeError("Task object is not callable")
