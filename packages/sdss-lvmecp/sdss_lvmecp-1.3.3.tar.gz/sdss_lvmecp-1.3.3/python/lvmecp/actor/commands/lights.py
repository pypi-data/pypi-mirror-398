#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-25
# @Filename: lights.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

import click

from . import parser


if TYPE_CHECKING:
    from lvmecp.actor import ECPCommand


@parser.command()
@click.argument(
    "ACTION",
    type=click.Choice(["on", "off", "toggle", "status"], case_sensitive=False),
    required=False,
)
@click.argument("LIGHT", type=str, required=False)
async def lights(
    command: ECPCommand,
    light: str | None = None,
    action: str | None = None,
):
    """Manages the enclosure lights."""

    plc = command.actor.plc

    if light is None or action == "status":
        await plc.lights.notify_status(wait=True, command=command)
        return command.finish()

    try:
        plc.lights.get_code(light)
    except ValueError:
        return command.fail(f"Unknown light {light}.")

    if action == "on":
        await plc.lights.on(light)
    elif action == "off":
        await plc.lights.off(light)
    elif action == "toggle":
        await plc.lights.toggle(light)

    await asyncio.sleep(0.1)

    await plc.lights.notify_status(wait=True, command=command)
    return command.finish()
