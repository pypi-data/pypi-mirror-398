#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2024-12-20
# @Filename: heartbeat.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from typing import TYPE_CHECKING

from . import parser


if TYPE_CHECKING:
    from lvmecp.actor import ECPCommand


@parser.command()
async def heartbeat(command: ECPCommand):
    """Sets the heartbeat variable on the PLC."""

    try:
        await command.actor.emit_heartbeat()
    except Exception:
        return command.fail("Failed to set heartbeat.")
    else:
        return command.finish()
