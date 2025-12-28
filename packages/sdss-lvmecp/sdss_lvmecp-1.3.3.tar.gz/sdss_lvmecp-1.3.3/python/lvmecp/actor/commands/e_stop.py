#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2025-01-07
# @Filename: e-stop.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

from . import parser


if TYPE_CHECKING:
    from lvmecp.actor import ECPCommand


@parser.command()
async def emergency_stop(command: ECPCommand):
    """Trigger and emergency stop."""

    await command.actor.plc.safety.emergency_stop()
    await asyncio.sleep(0.1)

    return command.finish(text="Emergency stop triggered.")
