#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: lights.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from lvmecp import log
from lvmecp.maskbits import LightStatus
from lvmecp.module import PLCModule


__all__ = ["LightsController", "CODE_TO_LIGHT", "CODE_TO_FLAG"]


CODE_TO_LIGHT = {
    "cr": "control_room",
    "sr": "spectrograph_room",
    "ur": "utilities_room",
    "uma": "uma_room",
    "tb": "telescope_bright",
    "tr": "telescope_red",
}

CODE_TO_FLAG = {
    "cr": LightStatus.CONTROL_ROOM,
    "sr": LightStatus.SPECTROGRAPH_ROOM,
    "ur": LightStatus.UTILITIES_ROOM,
    "uma": LightStatus.UMA_ROOM,
    "tb": LightStatus.TELESCOPE_BRIGHT,
    "tr": LightStatus.TELESCOPE_RED,
}


class LightsController(PLCModule):
    """Controller for the light settings."""

    flag = LightStatus
    interval = 30.0

    async def _update_internal(self, use_cache: bool = True, **kwargs):
        """Update status."""

        assert self.flag is not None

        light_registers = await self.plc.modbus.read_group(
            "lights",
            use_cache=use_cache,
        )

        active_bits = self.flag(0)
        for key in light_registers:
            if "status" in key and light_registers[key] is True:
                code = key.split("_")[0]
                active_bits |= CODE_TO_FLAG[code]

        return active_bits

    def get_code(self, light: str):
        """Returns the short-form code for a light. Case-insensitive.

        Parameters
        ----------
        light
            The light for which the code is seeked.

        Examples
        --------
        >>> get_code('telescope_red')
        'tr'
        >>> get_code('telescope bright')
        'tb'
        >>> get_code('uMa Room')
        'uma'

        Raises
        ------
        ValueError
            When a code cannot be found for the input light.

        """

        light = light.lower()

        if light in CODE_TO_LIGHT:
            return light

        for code, descr in CODE_TO_LIGHT.items():
            if light == descr:
                return code

            for repl in [" ", "-", ""]:
                if light == descr.replace("_", repl):
                    return code

        raise ValueError(f"Cannot find matching code for {light!r}.")

    def get_flag(self, light: str):
        """Gets the `.LightStatus` flag associated with a light.

        Parameters
        ----------
        light
            The light for which the `.LightStatus` a flag is requested. It can
            be specified in short form (e.g., ``tr``), using underscores
            (``telescope_red``), or spaces (``telescope red``). The light name
            is case-insensitive.

        """

        code = self.get_code(light)

        return CODE_TO_FLAG[code]

    async def toggle(self, light: str):
        """Switches a light."""

        code = self.get_code(light)

        log.debug(f"Toggling light {code}.")
        await self.modbus[f"{code}_new"].write(True)

        await asyncio.sleep(0.5)
        await self.update(use_cache=False)

    async def on(self, light: str):
        """Turns on a light."""

        assert self.status is not None

        await self.update(use_cache=False)

        flag = self.get_flag(light)
        if self.status & flag:
            return

        await self.toggle(light)

    async def off(self, light: str):
        """Turns off a light."""

        assert self.status is not None

        await self.update(use_cache=False)

        flag = self.get_flag(light)
        if not (self.status & flag):
            return

        await self.toggle(light)
