#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-05-08
# @Filename: module.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import abc
import asyncio

from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Coroutine,
    Generic,
    Sequence,
    Type,
    TypeVar,
)

from lvmecp import log
from lvmecp.tools import cancel_tasks_by_name


if TYPE_CHECKING:
    from lvmecp.maskbits import Maskbit
    from lvmecp.modbus import Modbus
    from lvmecp.plc import PLC

Flag_co = TypeVar("Flag_co", bound="Maskbit")


class PLCModule(abc.ABC, Generic[Flag_co]):
    """A module associated with a group of PLC variables."""

    flag: Type[Flag_co] | None = None
    interval: float | None = 10.0

    def __init__(
        self,
        name: str,
        plc: PLC,
        modbus: Modbus | None = None,
        interval: float | None = None,
        start: bool = True,
        notifier: Callable[[int, str, dict], Callable | Coroutine] | None = None,
    ):
        self.name = name
        self.plc = plc
        self.modbus = modbus or plc.modbus

        assert hasattr(self, "flag"), "flag not defined."

        self._interval = interval or self.interval
        self.status = self.flag(self.flag.__unknown__) if self.flag else None

        self.notifier = notifier

        self._update_loop_task: asyncio.Task | None = None
        if start:
            asyncio.create_task(self.start())

    def __del__(self):
        if hasattr(self, "_update_loop_task") and self._update_loop_task:
            try:
                self._update_loop_task.cancel()
            except RuntimeError:
                pass

    async def start(self):
        """Starts tracking the status of the PLC module."""

        await self.notify_status()

        if self._interval:
            self._update_loop_task = asyncio.create_task(self._status_loop())

    async def _status_loop(self):
        """Runs the status update loop."""

        assert self._interval is not None

        while True:
            await self.update(use_cache=False)
            await asyncio.sleep(self._interval)

    @abc.abstractmethod
    async def _update_internal(
        self,
        **kwargs,
    ) -> Flag_co | tuple[Flag_co, dict[str, Any]]:
        """Determines the new module flag status."""

        pass

    async def update(
        self,
        force_output: bool = False,
        use_cache: bool = True,
        **notifier_kwargs,
    ):
        """Refreshes the module status."""

        try:
            internal_output = await self._update_internal(use_cache=use_cache)
            if isinstance(internal_output, Sequence):
                new_status, extra_info = internal_output
            else:
                new_status, extra_info = internal_output, {}
        except Exception as err:
            log.warning(f"{self.name}: failed updating status: {err}")
            new_status = self.flag(self.flag.__unknown__) if self.flag else None
            extra_info = {}

        # Only notify if the status has changed.
        if (new_status != self.status and not extra_info) or force_output:
            await self.notify_status(
                new_status,
                extra_keywords=extra_info,
                **notifier_kwargs,
            )

        self.status = new_status

        return self.status

    async def notify_status(
        self,
        status: Flag_co | None = None,
        extra_keywords: dict[str, Any] = {},
        wait: bool = False,
        **kwargs,
    ):
        """Report the current status."""

        if self.notifier is None:
            return

        status = status if status is not None else self.status
        if status is None:
            return

        if asyncio.iscoroutinefunction(self.notifier):
            coro = self.notifier(status.value, str(status), extra_keywords, **kwargs)
            if wait:
                await coro
            else:
                # Find any other call and cancel it to avoid getting
                # outputs in the wrong order.
                name = f"notify_{self.name}"
                await cancel_tasks_by_name(name)
                asyncio.create_task(coro, name=name)
        else:
            asyncio.get_running_loop().call_soon(
                self.notifier,
                status.value,
                str(status),
                extra_keywords,
                **kwargs,
            )
