#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: simulator.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
from copy import deepcopy

from typing import Any, cast

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext,
    ModbusSparseDataBlock,
)
from pymodbus.server import ServerAsyncStop, StartAsyncTcpServer

from sdsstools.utils import cancel_task

from lvmecp import config


__all__ = ["Simulator", "plc_simulator"]


class Simulator:
    """A modbus simulator for a PLC controller."""

    def __init__(
        self,
        registers: dict,
        host: str = "127.0.0.1",
        port: int = 5020,
        overrides: dict[str, int | bool] = {},
        events: dict[str, dict[str, Any]] = {},
    ):
        self.host = host
        self.port = port

        self.registers = deepcopy(registers)

        self.overrides = overrides
        self.events = events

        self.context: ModbusServerContext | None = None
        self.slave_context: ModbusSlaveContext

        self.reset()
        self.context = ModbusServerContext(self.slave_context, single=True)

        self.__task: asyncio.Task | None = None

    def reset(self):
        di = {address: 0 for address in range(0, 1024)}
        co = {address: 0 for address in range(0, 1024)}
        hr = {address: 0 for address in range(0, 1024)}
        ir = {address: 0 for address in range(0, 1024)}

        for register in self.registers:
            mode = self.registers[register].get("mode", "coil")
            address = self.registers[register]["address"]
            value = self.overrides.get(register, 0)

            if mode == "coil":
                co[address] = value
            elif mode == "holding_register":
                hr[address] = value
            elif mode == "discrete_input":
                di[address] = value
            elif mode == "input_register":
                ir[address] = value
            else:
                raise ValueError(f"Invalid mode {mode!r} for register {register!r}.")

        self.slave_context = ModbusSlaveContext(
            di=ModbusSparseDataBlock(di),
            co=ModbusSparseDataBlock(co),
            hr=ModbusSparseDataBlock(hr),
            ir=ModbusSparseDataBlock(ir),
            zero_mode=True,
        )

        if self.context is not None:
            self.context[0] = self.slave_context

    async def start(self, monitor_interval: float = 0.01):
        """Starts the process that monitors changes and serves forever."""

        self.__task = asyncio.create_task(self._monitor_context(monitor_interval))

        await StartAsyncTcpServer(self.context, address=(self.host, self.port))

    async def stop(self):
        """Stops the simulator."""

        await ServerAsyncStop()

        self.__task = await cancel_task(self.__task)

    def __del__(self):
        if self.__task:
            self.__task.cancel()

    def get_register_data(self, register: str):
        """Returns the data for a register."""

        register_data = self.registers[register]

        address = register_data["address"]
        mode = register_data["mode"]

        if mode == "coil":
            code = 1
        elif mode == "holding_register":
            code = 3
        else:
            raise ValueError(f"Invalid mode {mode!r} for register {register!r}.")

        return {
            "name": register,
            "address": address,
            "mode": mode,
            "code": code,
            "value": int(self.slave_context.getValues(code, address, 1)[0]),
        }

    async def _monitor_context(self, interval: float):
        """Monitor the context."""

        assert self.context
        context = cast(ModbusSlaveContext, self.context[0])

        while True:
            for trigger_register, event_data in self.events.items():
                on_value: int | bool | None = event_data.get("on_value", None)
                if on_value is None:
                    continue

                trigger_data = self.get_register_data(trigger_register)

                if trigger_data["value"] != on_value:
                    continue

                then = event_data["then"]

                then_register_data = self.get_register_data(then["register"])
                if then["action"] == "toggle":
                    context.setValues(
                        then_register_data["code"],
                        then_register_data["address"],
                        [not then_register_data["value"]],
                    )
                elif then["action"] == "set":
                    context.setValues(
                        then_register_data["code"],
                        then_register_data["address"],
                        [1],
                    )
                elif then["action"] == "reset":
                    context.setValues(
                        then_register_data["code"],
                        then_register_data["address"],
                        [0],
                    )
                else:
                    continue

                if then.get("reset_trigger", True):
                    context.setValues(
                        trigger_data["code"],
                        trigger_data["address"],
                        [0],
                    )

            await asyncio.sleep(interval)


plc_simulator = Simulator(
    config["modbus"]["registers"],
    host=config["simulator"]["host"],
    port=config["simulator"]["port"],
    overrides=config["simulator"]["overrides"],
    events=config["simulator"]["events"],
)
