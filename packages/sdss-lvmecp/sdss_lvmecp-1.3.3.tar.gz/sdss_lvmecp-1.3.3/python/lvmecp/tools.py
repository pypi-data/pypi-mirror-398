#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: tools.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone

from typing import Any, AsyncGenerator, Callable, Coroutine, Literal

from redis import asyncio as aioredis


__all__ = [
    "loop_coro",
    "cancel_tasks_by_name",
    "timestamp_to_iso",
    "TimedCacheDict",
    "redis_client",
]


def loop_coro(
    coro: Coroutine[Any, Any, Any] | Callable[[], Any],
    interval: float = 1.0,
) -> asyncio.Task:
    """Creates a task that calls a function or coroutine on an interval."""

    async def _task_body():
        while True:
            if asyncio.iscoroutine(coro):
                await coro
            elif callable(coro):
                if asyncio.iscoroutinefunction(coro):
                    await coro()
                else:
                    coro()

            await asyncio.sleep(interval)

    return asyncio.create_task(_task_body())


async def cancel_tasks_by_name(name: str):
    """Cancels all tasks with ``name``."""

    tasks = [tasks for tasks in asyncio.all_tasks() if tasks.get_name() == name]
    for task in tasks:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


def timestamp_to_iso(ts: float | None, timespec: str = "seconds") -> str | None:
    """Converts a timestamp to an ISO string."""

    if ts is None or ts == 0:
        return None

    return (
        datetime.fromtimestamp(ts, timezone.utc)
        .isoformat(timespec=timespec)
        .replace("+00:00", "Z")
    )


class TimedCacheDict(dict):
    """A dictionary that caches values for a certain amount of time.

    Parameters
    ----------
    timeout
        The timeout in seconds for the cache.
    mode
        The mode for the cache. If ``delete``, the key will be deleted
        after the timeout. If ``null``, the value will be set to ``None``.

    """

    def __init__(self, timeout: float, mode: Literal["delete", "null"] = "delete"):
        self.timeout = timeout
        self.mode = mode

        self._cache_time: dict[str, float] = {}

        super().__init__()

    def freeze(self):
        """Returns a non-cached version of the dictionary."""

        return dict(self)

    def __getitem__(self, key: str):
        try:
            if time.time() - self._cache_time[key] > self.timeout:
                if self.mode == "delete":
                    del self[key]
                else:
                    self[key] = None
        except KeyError:
            pass

        return super().__getitem__(key)

    def __setitem__(self, key: str, value):
        self._cache_time[key] = time.time()
        super().__setitem__(key, value)

    def __delitem__(self, key: str):
        del self._cache_time[key]
        super().__delitem__(key)


@asynccontextmanager
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Returns a Redis connection."""

    client = aioredis.from_url("redis://localhost:6379/0", decode_responses=True)

    yield client

    await client.aclose()
