#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-06-20
# @Filename: safety.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import math
import time
from types import SimpleNamespace

from lvmecp.maskbits import SafetyStatus
from lvmecp.module import PLCModule


class SafetyController(PLCModule[SafetyStatus]):
    """Handles the enclosure safety features."""

    flag = SafetyStatus
    interval = 20.0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.o2_level_utilities: float = math.nan
        self.o2_level_spectrograph: float = math.nan

        self.last_heartbeat_ack: float | None = None

    async def _update_internal(self, use_cache: bool = True, **kwargs):
        assert self.flag is not None

        safety_registers = await self.plc.modbus.read_group(
            "safety",
            use_cache=use_cache,
        )

        safety_status = SimpleNamespace(**safety_registers)

        new_status = self.flag(0)

        # Door and lock
        if safety_status.door_closed:
            new_status |= self.flag.DOOR_CLOSED
        if safety_status.door_locked:
            new_status |= self.flag.DOOR_LOCKED
        if safety_status.local:
            new_status |= self.flag.LOCAL

        # Utilities room O2 sensor
        self.o2_level_utilities = safety_status.oxygen_read_utilities_room / 10.0
        if self.o2_level_utilities < self.plc.config["safety"]["o2_threshold"]:
            new_status |= self.flag.O2_SENSOR_UR_ALARM
        if safety_status.oxygen_error_code_utilities_room == 8:
            new_status |= self.flag.O2_SENSOR_UR_FAULT

        # Spectrograph room O2 sensor
        self.o2_level_spectrograph = safety_status.oxygen_read_spectrograph_room / 10.0
        if self.o2_level_spectrograph < self.plc.config["safety"]["o2_threshold"]:
            new_status |= self.flag.O2_SENSOR_SR_ALARM
        if safety_status.oxygen_error_code_spectrograph_room == 8:
            new_status |= self.flag.O2_SENSOR_SR_FAULT

        # Rain sensor
        if safety_status.rain_sensor_alarm:
            new_status |= self.flag.RAIN_SENSOR_ALARM

        # E-stop
        if safety_status.e_status:
            new_status |= self.flag.E_STOP

        # LN2 E-stop
        if safety_status.e_stop_ln2:
            new_status |= self.flag.E_STOP_LN2

        # Dome lockout and error
        if await self.plc.modbus["dome_lockout"].read():
            new_status |= self.flag.DOME_LOCKED
        if await self.plc.modbus["dome_error"].read():
            new_status |= self.flag.DOME_ERROR

        if new_status.value == 0:
            new_status = self.flag(self.flag.__unknown__)

        if await self.plc.modbus["hb_ack"].read():
            self.last_heartbeat_ack = time.time()

        return new_status

    async def is_remote(self):
        """Returns `True` if NOT in local mode (i.e., safe to operate remotely)."""

        await self.update()
        assert self.status is not None and self.flag is not None

        return not (self.status & self.flag.LOCAL)

    async def engineering_mode_active(self, include_plc_bypasses: bool = True):
        """Returns :obj:`True` if engineering mode is active.
        With ``include_plc_bypasses=True``, the function will return
        :obj:`True` if the lvmecp engineering mode is active or the PLC
        software or hardware bypasses are active.

        """

        if self.plc._actor is not None and self.plc._actor._eng_mode:
            return True

        if include_plc_bypasses is False:
            return False

        await self.update(use_cache=False)

        plc_hw = await self.plc.modbus.read_register("bypass_hardware_status")
        plc_sw = await self.plc.modbus.read_register("bypass_software_status")

        if plc_hw or plc_sw:
            return True

        return False

    async def emergency_stop(self):
        """Triggers an emergency stop."""

        await self.plc.modbus["e_stop"].write(True)

    async def reset_e_stops(self):
        """Resets the E-stop relays."""

        await self.plc.modbus["e_relay_reset"].write(True)
