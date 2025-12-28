#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2024-12-28
# @Filename: modbus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio

from typing import TYPE_CHECKING, Literal

import click

from lvmecp.modbus import ModbusRegister

from . import parser


if TYPE_CHECKING:
    from lvmecp.actor import ECPCommand
    from lvmecp.modbus import RegisterModes


def get_register(
    command: ECPCommand,
    address_or_name: str,
    register_type: RegisterModes | None = None,
    allow_unknown: bool = False,
) -> ModbusRegister | Literal[False]:
    """Returns a register from an address or name."""

    plc = command.actor.plc

    register: ModbusRegister | None = None
    address: int | None = None

    try:
        address = int(address_or_name)  # type: ignore

        if isinstance(address, int) and not register_type:
            command.fail("When passing an address, --register-type must be specified.")
            return False

        for _, reg in plc.modbus.items():
            if reg.address == address:
                register = reg
                break
    except ValueError:
        register = plc.modbus.get(address_or_name)
        address = register.address if register else None

    if register is None:
        if allow_unknown and address is not None and register_type:
            return ModbusRegister(
                command.actor.plc.modbus,
                name=f"{register_type}_{address}",
                address=address,
                mode=register_type,
                count=1,
                readonly=False,
            )

        command.fail(f"Register {address_or_name!r} not found.")
        return False

    return register


@parser.group()
def modbus():
    """Low-level access to the PLC Modbus variables."""

    pass


@modbus.command()
@click.argument("address", metavar="ADDRESS|NAME")
@click.option(
    "--register-type",
    type=click.Choice(["coil", "holding_register"]),
    default=None,
    help="The type of register to read. Required if an address is passed.",
)
@click.option(
    "--allow-unknown",
    is_flag=True,
    help="Allow unknown registers. Requires specifying an address.",
)
async def read(
    command: ECPCommand,
    address: str,
    register_type: Literal["coil", "holding_register"] | None = None,
    allow_unknown: bool = False,
):
    """Reads a Modbus register."""

    if not (
        register := get_register(
            command,
            address,
            register_type=register_type,
            allow_unknown=allow_unknown,
        )
    ):
        return False

    value = await register.read(use_cache=False)

    return command.finish(
        register={
            "name": register.name,
            "address": register.address,
            "value": value,
        }
    )


@modbus.command()
@click.argument("address", metavar="ADDRESS|NAME")
@click.argument("value", type=int)
@click.option(
    "--register-type",
    type=click.Choice(["coil", "holding_register"]),
    default=None,
    help="The type of register to read. Required if an address is passed.",
)
@click.option(
    "--allow-unknown",
    is_flag=True,
    help="Allow unknown registers. Requires specifying an address.",
)
async def write(
    command: ECPCommand,
    address: str,
    value: int,
    register_type: Literal["coil", "holding_register"] | None = None,
    allow_unknown: bool = False,
):
    """Writes a value to a Modbus register."""

    if not (
        register := get_register(
            command,
            address,
            register_type=register_type,
            allow_unknown=allow_unknown,
        )
    ):
        return False

    name = register.name

    if register.readonly:
        return command.fail(f"Register {name!r} is read-only.")

    if register.mode == "coil":
        value = bool(int(value))
    else:
        value = int(value)

    try:
        await register.write(value)
    except Exception as err:
        return command.fail(f"Error writing to register {name!r}: {err!r}")

    await asyncio.sleep(0.5)
    new_value = await register.read(use_cache=False)

    return command.finish(
        register={
            "name": name,
            "address": register.address,
            "value": new_value,
        }
    )
