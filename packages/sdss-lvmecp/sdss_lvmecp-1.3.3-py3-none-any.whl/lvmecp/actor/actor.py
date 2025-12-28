#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: actor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import time

from lvmopstools.actor import ErrorCodesBase, LVMActor
from lvmopstools.notifications import send_notification

from sdsstools.utils import cancel_task

from lvmecp import __version__, log
from lvmecp.actor.commands import parser
from lvmecp.maskbits import DomeStatus
from lvmecp.plc import PLC
from lvmecp.tools import redis_client


__all__ = ["ECPActor"]


class ECPActor(LVMActor):
    """Enclosure actor."""

    parser = parser

    def __init__(
        self,
        plc: PLC | None = None,
        *args,
        plc_config: dict | None = None,
        **kwargs,
    ):
        if "version" not in kwargs:
            kwargs["version"] = __version__

        super().__init__(*args, **kwargs)

        if self.log.log_filename and self.log.fh:
            log.addHandler(self.log.fh)

        if plc is None:
            plc_config = plc_config or self.config
            self.plc = PLC(config=plc_config, actor=self, start_modules=False)
        else:
            self.plc = plc

        self._emit_status_task: asyncio.Task | None = None
        self._monitor_dome_task: asyncio.Task | None = None
        self._monitor_internet_task: asyncio.Task | None = None

        self._eng_mode: bool = False
        self._eng_mode_hearbeat_interval: float = 5
        self._eng_mode_started_at: float = 0
        self._eng_mode_duration: float = 0
        self._eng_mode_task: asyncio.Task | None = None

        self.running: bool = False

    async def start(self, **kwargs):
        """Starts the actor."""

        await super().start(**kwargs)
        self.running = True

        await self.plc.read_all_registers(use_cache=False)

        # Start PLC modules now that the actor is running. This prevents the modules
        # trying to broadcast messages before the actor is ready.
        await self.plc.start_modules()

        self._emit_status_task = asyncio.create_task(self.emit_status())
        self._monitor_dome_task = asyncio.create_task(self.monitor_dome())
        self._monitor_internet_task = asyncio.create_task(self.monitor_internet())

        try:
            await self._restore_eng_mode()
        except Exception as err:
            log.error(f"Failed restoring engineering mode: {err}")

        return self

    async def stop(self, **kwargs):
        """Stops the actor."""

        self._emit_status_task = await cancel_task(self._emit_status_task)
        self._monitor_dome_task = await cancel_task(self._monitor_dome_task)
        self._monitor_internet_task = await cancel_task(self._monitor_internet_task)

        self._eng_mode_task = await cancel_task(self._eng_mode_task)

        await super().stop(**kwargs)
        self.running = False

        return

    async def emit_status(self, delay: float = 30.0):
        """Emits the status on a timer."""

        while True:
            await self.send_command(self.name, "status", internal=True)
            await asyncio.sleep(delay)

    async def monitor_internet(self, delay: float = 30.0):
        """Monitors the internet connection and set the PLC variable."""

        while True:
            await asyncio.sleep(delay)

            try:
                beat_cmd = await self.send_command(
                    "lvmbeat",
                    "status",
                    internal=True,
                    time_limit=5,
                )
                network = beat_cmd.replies.get("network")

                if not network.get("internet", True) or not network.get("lco", True):
                    # No internet or LCO connection
                    await self.plc.modbus["network_failure"].write(True)
                else:
                    await self.plc.modbus["network_failure"].write(False)

            except Exception as err:
                log.error(f"Failed determining network status: {err}")

    async def monitor_dome(self, delay: float = 30.0):
        """Monitors the dome and closes during daytime."""

        while True:
            await asyncio.sleep(delay)

            closing_flags = DomeStatus.MOTOR_CLOSING | DomeStatus.CLOSED
            is_closing = self.plc.dome.status and (self.plc.dome.status & closing_flags)

            # Check engineering mode. This includes the PLC overrides.
            eng_mode = await self.plc.safety.engineering_mode_active()
            if eng_mode:
                pass
            elif self.plc.dome.is_daytime() and not is_closing:
                try:
                    self.write("w", text="Dome found open during daytime. Closing.")
                    await send_notification(
                        "Dome found open during daytime. Closing.",
                        level="warning",
                    )
                except Exception as err:
                    log.error(f"Failed notifying about daytime dome closure: {err}")
                finally:
                    try:
                        await self.plc.dome.close()
                    except Exception as err:
                        self.write("e", error=f"Failed closing dome: {err}")

    async def eng_mode(self, enable: bool, timeout: float | None = None):
        """Sets or returns the engineering mode."""

        # Kill current task if it exists.
        self._eng_mode_task = await cancel_task(self._eng_mode_task)

        if enable:
            self._eng_mode_task = asyncio.create_task(self._run_eng_mode(timeout))
        else:
            self._eng_mode_task = await cancel_task(self._eng_mode_task)
            self._eng_mode_started_at = 0
            self._eng_mode_duration = 0

        self._eng_mode = enable

    def is_eng_mode_enabled(self):
        """Returns whether engineering mode is enabled."""

        return self._eng_mode

    async def _run_eng_mode(self, timeout: float | None = None):
        """Runs the engineering mode.

        Emits a heartbeat every N seconds even if we are not receiving heartbeat
        commands from ``lvmbeat``. Monitors how long we have been in engineering
        mode and disables it after a timeout.

        """

        eng_mode_config = self.config.get("engineering_mode", {})
        default_duration = eng_mode_config.get("default_duration", 300)

        self._eng_mode = True
        self._eng_mode_started_at = time.time()
        self._eng_mode_duration = timeout or default_duration

        while True:
            if not self._eng_mode:
                await self.eng_mode(False)
                return

            await self.emit_heartbeat()

            elapsed = time.time() - self._eng_mode_started_at

            if elapsed > self._eng_mode_duration:
                self.write("w", text="Engineering mode timed out and was disabled.")
                await self.eng_mode(False)
                return

            await asyncio.sleep(self._eng_mode_hearbeat_interval)

    async def _restore_eng_mode(self):
        """Restores the engineering mode from Redis."""

        # Get data from Redis.
        async with redis_client() as redis:
            eng_mode = await redis.get("lvmecp.eng_mode")
            eng_mode_started_at = await redis.get("lvmecp.eng_mode_started_at")
            eng_mode_duration = await redis.get("lvmecp.eng_mode_duration")
            eng_mode_hw_bypass = await redis.get("lvmecp.bypass_hardware_remote")
            eng_mode_sw_bypass = await redis.get("lvmecp.bypass_software_remote")

        if eng_mode is not None:
            self._eng_mode = bool(int(eng_mode))

            if eng_mode and eng_mode_started_at and eng_mode_duration:
                now = time.time()
                end_time = float(eng_mode_started_at) + float(eng_mode_duration)
                duration = end_time - now
                if duration < 0:
                    self._eng_mode = False
                    return

                self._eng_mode_task = asyncio.create_task(self._run_eng_mode(duration))
                return

            self._eng_mode = False

            modbus = self.plc.modbus
            await modbus.write_register("bypass_hardware_remote", eng_mode_hw_bypass)
            await modbus.write_register("bypass_software_remote", eng_mode_sw_bypass)

    async def emit_heartbeat(self):
        """Emits a heartbeat to the PLC."""

        self.log.debug("Emitting heartbeat to the PLC.")
        await self.plc.modbus["hb_set"].write(True)

    async def _check_internal(self):
        return await super()._check_internal()

    async def _troubleshoot_internal(
        self,
        error_code: ErrorCodesBase,
        exception: Exception | None = None,
    ):
        return await super()._troubleshoot_internal(error_code, exception)
