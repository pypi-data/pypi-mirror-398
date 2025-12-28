#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: plc.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, Any

from lvmecp.hvac import HVACController
from lvmecp.modbus import Modbus
from lvmecp.safety import SafetyController

from .dome import DomeController
from .lights import LightsController


if TYPE_CHECKING:
    from clu.command import Command

    from .actor import ECPActor


def create_actor_notifier(
    actor: ECPActor | None,
    keyword: str,
    use_hex: bool = True,
    labels_suffix="_labels",
    level="d",
    allow_broadcasts: bool = False,
):
    """Generate a notifier function for a keyword."""

    async def notifier(
        value: int,
        labels: str,
        extra_keywords: dict[str, Any] = {},
        command: Command | None = None,
    ):
        message = {
            keyword: value if use_hex is False else hex(value),
            f"{keyword}{labels_suffix}": labels,
        }
        message.update(extra_keywords)

        if command is None and actor and allow_broadcasts:
            # Allow for 3 seconds for broadcast. This is needed because the PLC
            # starts before the actor and for the first message the exchange is
            # not yet available.
            elapsed: float = 0
            while not actor.running:
                elapsed += 0.01
                if elapsed > 3:
                    return
                await asyncio.sleep(0.01)
            actor.write(level, message)
        elif command is not None:
            command.write(level, message)

    return notifier if actor else None


class PLC:
    """Class for the enclosure programmable logic controller."""

    def __init__(
        self,
        config: dict,
        actor: ECPActor | None = None,
        start_modules: bool = True,
    ):
        self.config = config
        self.modbus = Modbus(config=config["modbus"])

        self._actor = actor

        self.dome = DomeController(
            "dome",
            self,
            notifier=create_actor_notifier(actor, "dome_status"),
            start=start_modules,
        )

        self.safety = SafetyController(
            "safety",
            self,
            notifier=create_actor_notifier(actor, "safety_status"),
            start=start_modules,
        )

        self.lights = LightsController(
            "lights",
            self,
            notifier=create_actor_notifier(actor, "lights"),
            start=start_modules,
        )

        self.hvac_modbus = Modbus(config=config["hvac"])
        self.hvac = HVACController(
            "hvac",
            self,
            modbus=self.hvac_modbus,
            notifier=None,
            start=start_modules,
        )

    async def start_modules(self):
        """Starts all the modules."""

        await asyncio.gather(
            self.dome.start(),
            self.safety.start(),
            self.lights.start(),
            self.hvac.start(),
        )

    async def read_all_registers(self, use_cache: bool = True):
        """Reads all the connected registers and returns a dictionary."""

        registers_plc, registers_hvac = await asyncio.gather(
            self.modbus.read_all(use_cache=use_cache),
            self.hvac_modbus.read_all(use_cache=use_cache),
        )

        return registers_plc | registers_hvac
