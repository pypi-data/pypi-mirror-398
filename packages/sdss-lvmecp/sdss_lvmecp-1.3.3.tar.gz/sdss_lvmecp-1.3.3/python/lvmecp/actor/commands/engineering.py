#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2024-12-24
# @Filename: engineering.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING

import click

from lvmecp.tools import redis_client, timestamp_to_iso

from . import parser


if TYPE_CHECKING:
    from lvmecp.actor import ECPActor, ECPCommand


async def get_eng_mode_status(actor: ECPActor) -> dict:
    enabled = actor.is_eng_mode_enabled()
    started_at = actor._eng_mode_started_at
    duration = actor._eng_mode_duration

    registers = await actor.plc.read_all_registers(use_cache=False)

    if duration is None or started_at is None:
        ends_at = None
    else:
        ends_at = started_at + duration

    sw_bypass = registers["bypass_software_status"]
    sw_is_remote = sw_bypass and registers["bypass_software_remote"]
    sw_bypass_mode = "none" if not sw_bypass else "remote" if sw_is_remote else "local"

    hw_bypass = registers["bypass_hardware_status"]
    hw_is_remote = hw_bypass and registers["bypass_hardware_remote"]
    hw_bypass_mode = "none" if not hw_bypass else "remote" if hw_is_remote else "local"

    return {
        "enabled": enabled,
        "started_at": timestamp_to_iso(started_at),
        "ends_at": timestamp_to_iso(ends_at),
        "plc_software_bypass": sw_bypass,
        "plc_hardware_bypass": hw_bypass,
        "plc_software_bypass_mode": sw_bypass_mode,
        "plc_hardware_bypass_mode": hw_bypass_mode,
    }


@parser.group(name="engineering-mode")
def engineering_mode():
    """Enable/disable the engineering mode."""

    pass


@engineering_mode.command()
@click.option(
    "--timeout",
    "-t",
    type=click.FloatRange(min=0, max=300),
    help="Timeout for the engineering mode, in hours. "
    "If not passed, the default timeout is used.",
)
@click.option(
    "--hardware-bypass",
    is_flag=True,
    help="Sets the hardware bypass flag.",
)
@click.option(
    "--software-bypass",
    is_flag=True,
    help="Sets the software bypass flag.",
)
async def enable(
    command: ECPCommand,
    timeout: float | None = None,
    hardware_bypass: bool = False,
    software_bypass: bool = False,
):
    """Enables the engineering mode."""

    actor = command.actor
    modbus = command.actor.plc.modbus

    if timeout is not None:
        timeout = timeout * 3600

    await command.actor.eng_mode(True, timeout=timeout)
    await asyncio.sleep(0.5)  # Allow time for the e-mode task to run.

    if hardware_bypass:
        await modbus.write_register("bypass_hardware_remote", True)
    if software_bypass:
        await modbus.write_register("bypass_software_remote", True)

    try:
        # Safe the engineering mode data to Redis so that we can recover it
        # if the actor restarts.
        async with redis_client() as redis:
            await redis.set("lvmecp.eng_mode", 1)
            await redis.set("lvmecp.eng_mode_started_at", actor._eng_mode_started_at)
            await redis.set("lvmecp.eng_mode_duration", actor._eng_mode_duration)
            await redis.set("lvmecp.bypass_hardware_remote", int(hardware_bypass))
            await redis.set("lvmecp.bypass_software_remote", int(software_bypass))
    except Exception as err:
        command.error(f"Failed saving engineering mode to Redis: {err}")

    return command.finish(engineering_mode=await get_eng_mode_status(command.actor))


@engineering_mode.command()
async def disable(command: ECPCommand):
    """Disables the engineering mode."""

    modbus = command.actor.plc.modbus

    await command.actor.eng_mode(False)

    await modbus.write_register("bypass_hardware_remote", False)
    await modbus.write_register("bypass_software_remote", False)

    try:
        # Safe the engineering mode data to Redis so that we can recover it
        # if the actor restarts.
        async with redis_client() as redis:
            await redis.set("lvmecp.eng_mode", 0)
            await redis.set("lvmecp.eng_mode_started_at", 0)
            await redis.set("lvmecp.eng_mode_duration", 0)
            await redis.set("lvmecp.bypass_hardware_remote", 0)
            await redis.set("lvmecp.bypass_software_remote", 0)
    except Exception as err:
        command.error(f"Failed saving engineering mode to Redis: {err}")

    return command.finish(engineering_mode=await get_eng_mode_status(command.actor))


@engineering_mode.command()
async def status(command: ECPCommand):
    """Returns the status of the engineering mode."""

    return command.finish(engineering_mode=await get_eng_mode_status(command.actor))


@engineering_mode.command()
async def reset_e_stops(command: ECPCommand):
    """Resets the e-stop relays."""

    await command.actor.plc.safety.reset_e_stops()

    return command.finish()
