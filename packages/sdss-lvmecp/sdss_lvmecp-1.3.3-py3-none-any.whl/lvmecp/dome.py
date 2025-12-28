#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: dome.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
from time import time
from types import SimpleNamespace

from typing import Literal

import numpy
from astropy.time import Time
from lvmopstools.ephemeris import get_ephemeris_summary

from lvmecp import config, log
from lvmecp.exceptions import DomeError
from lvmecp.maskbits import DomeStatus, SafetyStatus
from lvmecp.module import PLCModule


MOVE_CHECK_INTERVAL: float = 0.5
AFTER_STOP_DELAY: float = 5

DRIVE_MODE_TYPE = Literal["normal", "overcurrent"]


class DomeController(PLCModule[DomeStatus]):
    """Controller for the rolling dome."""

    flag = DomeStatus
    interval = 15.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Timestamps when we have opened the dome. For the anti-flap mechanism.
        self._open_attempt_times: list[float] = []

    async def _update_internal(self, use_cache: bool = True, **kwargs):
        dome_registers = await self.plc.modbus.read_group("dome", use_cache=use_cache)

        dome_status = SimpleNamespace(**dome_registers)

        assert self.flag
        new_status = self.flag(0)

        # The variable that would determine if the drive is available is not
        # does not exist any more, so we assume it is.
        new_status |= self.flag.DRIVE_AVAILABLE

        if dome_status.dome_error or dome_status.drive_status1 > 0:
            new_status |= self.flag.DRIVE_ERROR

        if dome_status.drive_enabled:
            new_status |= self.flag.DRIVE_ENABLED
            new_status |= self.flag.MOVING
            if dome_status.motor_direction:
                new_status |= self.flag.MOTOR_OPENING
            else:
                new_status |= self.flag.MOTOR_CLOSING

        if dome_status.dome_open is True:
            new_status |= self.flag.OPEN
        elif dome_status.dome_closed is True:
            new_status |= self.flag.CLOSED
        else:
            new_status |= self.flag.POSITION_UNKNOWN

        if new_status.value == 0:
            new_status = self.flag(self.flag.__unknown__)

        if dome_status.dome_open:
            percent_open = 1
        elif dome_status.dome_closed:
            percent_open = 0
        else:
            full_open = config["dome.full_open_mm"]
            percent_open = numpy.clip(dome_status.dome_position / full_open, 0, 1)

        extra_info = {
            "dome_percent_open": round(float(percent_open) * 100, 1),
        }

        return new_status, extra_info

    async def set_direction(self, open: bool):
        """Sets the motor direction (`True` means open, `False` close)."""

        await self.modbus["drive_direction"].write(open)
        await self.update(use_cache=False)

    async def _move(
        self,
        open: bool,
        force: bool = False,
        mode: DRIVE_MODE_TYPE = "normal",
    ):
        """Moves the dome to open/close position."""

        if mode == "overcurrent" and open:
            raise DomeError("Cannot open dome in overcurrent mode.")

        await self.update(use_cache=False)
        await self.plc.safety.update(use_cache=False)

        # Check safety flags.

        if not (await self.plc.safety.is_remote()):
            raise DomeError("Cannot move dome while in local mode.")

        if not self.plc.safety.status or self.plc.safety.status & SafetyStatus.E_STOP:
            raise DomeError("E-stops are pressed.")

        assert self.status is not None and self.flag is not None

        if self.status & self.flag.UNKNOWN:
            raise DomeError("Dome is in unknown state.")

        if self.status & self.flag.NODRIVE:
            raise DomeError("Dome drive is not available.")

        # Check drive errors.
        if self.status & self.flag.DRIVE_ERROR:
            raise DomeError(
                "Dome drive is in error state. Please check "
                "the drive and reset the error state if appropriate."
            )

        if self.status & self.flag.DRIVE_ENABLED:
            # Dome is moving.

            opening = bool(self.status & self.flag.MOTOR_OPENING)
            closing = bool(self.status & self.flag.MOTOR_CLOSING)

            # If the dome is moving ing the right direction, do nothing.
            if (open and opening) or (not open and closing):
                log.info("Dome is already moving in the commanded direction.")
                await self._wait_until_movement_done(open)
                return

            # Otherwise we stop the move and wait a bit for things to clear.
            log.warning("Stopping the dome before moving to the commanded position.")
            await self.stop()

        already_at_position = False
        if (self.status & self.flag.OPEN) and open:
            already_at_position = True
        elif (self.status & self.flag.CLOSED) and not open:
            already_at_position = True
        else:
            log.warning("Dome in unknown or intermediate position.")

        if already_at_position:
            if force is False:
                return
            log.warning("Dome already at position but forcing.")

        if mode == "normal":
            log.debug("Setting drive mode to normal.")
            await self.modbus["drive_mode_overcurrent"].write(0)
        elif mode == "overcurrent":
            log.debug("Setting drive mode to overcurrent.")
            await self.modbus["drive_mode_overcurrent"].write(1)

        log.debug("Setting motor_direction.")
        await self.modbus["motor_direction"].write(open)

        await asyncio.sleep(0.1)

        log.debug("Setting drive_enabled.")
        await self.modbus["drive_enabled"].write(True)

        await asyncio.sleep(0.1)

        # Wait until the dome finishes to move, with a timeout.
        await self._wait_until_movement_done(open)

        # Reset drive_mode_overcurrent.
        await self.modbus["drive_mode_overcurrent"].write(0)

        await self.update(use_cache=False)

    async def _wait_until_movement_done(self, open: bool, timeout: float = 300):
        """Blocks until the dome has finished moving."""

        elapsed: float = 0.0
        last_enabled: float = 0.0
        while True:
            await asyncio.sleep(MOVE_CHECK_INTERVAL)
            elapsed += MOVE_CHECK_INTERVAL

            if elapsed >= timeout:
                raise DomeError("Timeout waiting for dome to finish moving.")

            drive_enabled = await self.modbus["drive_enabled"].read(use_cache=False)

            move_done_register = self.modbus["dome_open" if open else "dome_closed"]
            move_done = await move_done_register.read(use_cache=False)

            if drive_enabled:
                last_enabled = time()

            if not drive_enabled and move_done:
                break

            # Check if the drive is not enabled for more than 5 seconds without the
            # movement being done. This usually means the dome has been manually
            # stopped.
            if not drive_enabled and (time() - last_enabled) > 5:
                raise DomeError("Dome drive has been disabled.")

    async def open(self, force: bool = False):
        """Open the dome."""

        self._open_attempt_times.append(time())

        if not await self.allowed_to_open():
            raise DomeError("Dome is not allowed to open.")

        await self._move(True, force=force)

    async def close(self, force: bool = False, mode: DRIVE_MODE_TYPE = "normal"):
        """Close the dome."""

        await self._move(False, force=force, mode=mode)

    async def stop(self):
        """Stops the dome."""

        status = await self.update(use_cache=False)
        if status is None or self.flag is None:
            raise RuntimeError("Failed retrieving dome status.")

        drive_enabled = bool(status & self.flag.DRIVE_ENABLED)
        if not drive_enabled:
            return

        await self.plc.modbus["drive_enabled"].write(False)
        await asyncio.sleep(AFTER_STOP_DELAY)

        await self.update(use_cache=False)

    async def reset(self):
        """Resets the roll-off error state."""

        await self.modbus["dome_error_reset"].write(True)
        await asyncio.sleep(0.5)

    async def allowed_to_open(self):
        """Returns whether the dome is allowed to move."""

        if await self.plc.safety.engineering_mode_active():
            if actor := self.plc._actor:
                actor.write("w", text="Engineering mode active. Skipping dome checks.")
            return True

        if not config["dome.daytime_allowed"] and self.is_daytime():
            raise DomeError("Dome is not allowed to open during daytime.")

        anti_flap_n, anti_flap_interval = config["dome.anti_flap_tolerance"] or [3, 600]

        attempts_in_interval: list[float] = []
        for tt in self._open_attempt_times[::-1]:
            if time() - tt < anti_flap_interval:
                attempts_in_interval.append(tt)
            else:
                break

        if len(attempts_in_interval) >= anti_flap_n:
            raise DomeError(
                "Too many open attempts in a short interval. "
                f"Wait {anti_flap_interval} seconds before trying again."
            )

        return True

    def is_daytime(self):  # pragma: no cover
        """Returns whether it is daytime."""

        daytime_tolerance = config["dome.daytime_tolerance"] or 0.0

        ephemeris = get_ephemeris_summary()
        sunset = ephemeris["sunset"] - daytime_tolerance / 86400
        sunrise = ephemeris["sunrise"] + daytime_tolerance / 86400

        now = Time.now().jd
        assert isinstance(now, float)

        if now < sunset or now > sunrise:
            return True

        return False
