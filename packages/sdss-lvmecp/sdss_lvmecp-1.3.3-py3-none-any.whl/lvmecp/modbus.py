#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-05-23
# @Filename: modbus.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import pathlib
from time import time

from typing import Any, Literal, Sequence

from lvmopstools.retrier import Retrier
from pymodbus.client.tcp import AsyncModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from sdsstools import Configuration, read_yaml_file
from sdsstools.utils import cancel_task

from lvmecp import config as lvmecp_config
from lvmecp import log
from lvmecp.exceptions import ECPError
from lvmecp.tools import TimedCacheDict


MAX_RETRIES = 3
MAX_COUNT_HR = 100
CONNECTION_TIMEOUT = 10.0


RegisterModes = Literal["coil", "holding_register", "discrete_input", "input_register"]


class ModbusRegister:
    """A Modbus register/variable.

    Parameters
    ----------
    modbus
        The `.Modbus` connection.
    name
        The name assigned to this register.
    address
        The PDU ``address`` (note this is 0-indexed, and one less than the
        register in the memory block) for the element.
    mode
        The type of data block: `coil``, ``holding_register``, ``discrete_input``,
        or ``input_register``.
    group
        A grouping key for registers.
    readonly
        Whether the register is read-only.

    """

    def __init__(
        self,
        modbus: Modbus,
        name: str,
        address: int,
        mode: RegisterModes = "coil",
        count: int = 1,
        group: str | None = None,
        decoder: str | None = None,
        readonly: bool = True,
    ):
        self.modbus: Modbus = modbus
        self.client: AsyncModbusTcpClient = modbus.client

        self.name: str = name
        self.address: int = address
        self.mode: RegisterModes = mode
        self.count: int = count
        self.group: str | None = group
        self.decoder: str | None = decoder
        self.readonly: bool = readonly

    async def _read_internal(self):
        """Return the value of the modbus register."""

        if self.mode == "coil":
            func = self.client.read_coils
        elif self.mode == "holding_register":
            func = self.client.read_holding_registers
        elif self.mode == "discrete_input":
            func = self.client.read_discrete_inputs
        elif self.mode == "input_register":
            func = self.client.read_input_registers
        else:
            raise ValueError(f"Invalid block mode {self.mode!r}.")

        async with self.modbus:
            resp = await func(
                self.address,
                count=self.count,
                slave=self.modbus.slave,
            )

        if resp.isError():
            raise ValueError(
                f"Invalid response for element "
                f"{self.name!r}: 0x{resp.function_code:02X}."
            )

        if self.mode == "coil" or self.mode == "discrete_input":
            bits = resp.bits
            value = bits[0 : self.count] if self.count > 1 else bits[0]
        else:
            registers = resp.registers
            value = registers[0 : self.count] if self.count > 1 else registers[0]

        # Apply any overrides from the configuration.
        if self.name in self.modbus.overrides:
            value = self.modbus.overrides[self.name]

        value = self.decode(value)

        if not isinstance(value, (int, float)):
            raise ValueError(f"Invalid type for {self.name!r} response.")

        return value

    def decode(
        self,
        value: int | bool | list[int | bool],
    ) -> int | bool | list[int | bool]:
        """Decodes the raw value from the register."""

        if self.decoder is not None:
            if self.decoder == "float_32bit":
                bin_payload = BinaryPayloadDecoder.fromRegisters(
                    value,
                    byteorder=Endian.BIG,
                    wordorder=Endian.LITTLE,
                )
                value = round(bin_payload.decode_32bit_float(), 3)
            else:
                raise ValueError(f"Unknown decoder {self.decoder}")

        return value

    @Retrier(max_attempts=MAX_RETRIES, delay=0.5, max_delay=2.0)
    async def read(self, use_cache: bool = True):
        """Return the value of the modbus register.

        Parameters
        ----------
        use_cache
            Whether to use the cache to retrieve the value. If the cache is not
            available, or the value is not in the cache, the register will be read.
            This function does not set the cache after reading the register.

        """

        if use_cache:
            cache = self.modbus.register_cache
            if self.name in cache and (value := cache[self.name]) is not None:
                return value

        return await self._read_internal()

    @Retrier(max_attempts=MAX_RETRIES, delay=0.5, max_delay=2.0)
    async def write(self, value: int | bool):
        """Sets the value of the register."""

        if self.readonly:
            raise ECPError(f"Register {self.name!r} is read-only.")

        if self.mode == "coil":
            func = self.client.write_coil
        elif self.mode == "holding_register":
            func = self.client.write_register
        elif self.mode == "discrete_input" or self.mode == "input_register":
            raise ValueError(f"Block of mode {self.mode!r} is read-only.")
        else:
            raise ValueError(f"Invalid block mode {self.mode!r}.")

        # Always open the connection.
        async with self.modbus:
            resp = await func(self.address, value)  # type: ignore

            if resp.isError():
                raise ECPError(
                    f"Invalid response for element "
                    f"{self.name!r}: 0x{resp.function_code:02X}."
                )
            else:
                self.modbus.register_cache[self.name] = value
                log.debug(
                    f"Written value {value} to register {self.name!r} "
                    f"({self.mode}-{self.address})."
                )


class Modbus(dict[str, ModbusRegister]):
    """A simple dictionary of Modbus registers.

    Parameters
    ----------
    config
        A YAML configuration file or dictionary with the keys ``host`` and ``port``
        for the Modbus server, and a dictionary ``registers`` with modbus registers.
        Each one must include a PDU ``address`` (note this is 0-indexed, and one
        less than the register in the memory block) and optionally ``mode`` for
        the block type (``coil``, ``holding_register``, ``discrete_input``,
        or ``input_register``; defaults to ``coil``). If `None`, defaults to the
        internal configuration.

    """

    def __init__(self, config: dict | pathlib.Path | str | None = None):
        if isinstance(config, (str, pathlib.Path)):
            self.config = read_yaml_file(
                str(config),
                return_class=Configuration,
            )["modbus"]
        elif config is None:
            self.config = lvmecp_config["modbus"]
        elif isinstance(config, dict):
            self.config = config

        assert isinstance(self.config, dict)

        self.host = self.config["host"]
        self.port = self.config["port"]
        self.slave = self.config.get("slave", 0)

        # Cache results so that very close calls to get_all()
        # don't need to open a connection and read the registers.
        self.cache_timeout = self.config.get("cache_timeout", 1)
        self.register_cache = TimedCacheDict(self.cache_timeout, mode="null")

        # Register overrides
        self.overrides: dict[str, Any] = self.config.get("overrides", {}) or {}

        # Modbus client.
        self.client = AsyncModbusTcpClient(self.host, port=self.port)

        # Lock to allow up to 5 concurrent connections.
        self.lock = asyncio.Lock()
        self._lock_release_task: asyncio.Task | None = None

        # Create the internal dictionary of registers
        registers = {
            name: ModbusRegister(
                self,
                name,
                register["address"],
                mode=register.get("mode", "coil"),
                group=register.get("group", None),
                count=register.get("count", 1),
                decoder=register.get("decoder", None),
                readonly=register.get("readonly", True),
            )
            for name, register in self.config["registers"].items()
        }

        dict.__init__(self, registers)
        for name, register in registers.items():
            setattr(self, name, register)

        log.debug(
            f"Modbus connection to {self.host}:{self.port} initialised "
            f"with cache timeout {self.cache_timeout} seconds."
        )

    async def connect(self):
        """Connects to the client."""

        try:
            await asyncio.wait_for(self.lock.acquire(), CONNECTION_TIMEOUT)
        except asyncio.TimeoutError:
            raise RuntimeError("Timed out waiting for lock to be released.")

        hp = f"{self.host}:{self.port}"

        did_connect: bool = False

        try:
            await asyncio.wait_for(self.client.connect(), timeout=5)
            did_connect = True
        except asyncio.TimeoutError:
            raise ConnectionError(f"Timed out connecting to server at {hp}.")
        except Exception as err:
            raise ConnectionError(f"Failed connecting to server at {hp}: {err}.")
        finally:
            if not did_connect and self.lock.locked():
                self.lock.release()

        # Schedule a task to release the lock after 5 seconds. This is a safeguard
        # in case something fails and the connection is never closed and the lock
        # not released.
        self._lock_release_task = asyncio.create_task(self.unlock_on_timeout())

    async def disconnect(self):
        """Disconnects the client."""

        try:
            if self.client:
                self.client.close()

        finally:
            if self.lock.locked():
                self.lock.release()

            await cancel_task(self._lock_release_task)

    async def __aenter__(self):
        """Initialises the connection to the server."""

        await self.connect()

    async def __aexit__(self, exc_type, exc, tb):
        """Closes the connection to the server."""

        await self.disconnect()

    async def unlock_on_timeout(self):
        """Removes the lock after an amount of time."""

        await asyncio.sleep(CONNECTION_TIMEOUT)
        await self.disconnect()

    async def read_all(self, use_cache: bool = True) -> dict[str, int | bool]:
        """Returns a dictionary with all the registers and sets the cache."""

        if use_cache:
            cache_times = self.register_cache._cache_time.values()
            oldest_cache = min(cache_times) if len(cache_times) > 0 else 0
            if time() - oldest_cache < self.cache_timeout:
                return self.register_cache.freeze()

        # With this PLC it is more efficient to read the entire coil and
        # holding register blocks in one go, and then parse the results, as
        # opposed to reading each register individually.
        async with self:
            for mode in ["coil", "holding_register"]:
                mode_count = max(
                    register.address + register.count
                    for register in self.values()
                    if register.mode == mode
                )

                if mode == "coil":
                    func = self.client.read_coils
                elif mode == "holding_register":
                    func = self.client.read_holding_registers
                else:
                    raise ValueError(f"Invalid mode {mode!r}.")

                data: list[int | bool] = []

                if mode == "coil":
                    # For coils we can read the entire block.
                    resp = await func(0, count=1023, slave=self.slave)

                    if resp.isError():
                        raise ValueError(
                            f"Invalid response for block {mode!r}: "
                            f"0x{resp.function_code:02X}."
                        )

                    data += resp.bits

                else:
                    # For holding registers we are limited to reading MAX_COUNT_HR
                    # at once. We iterate to get all the data.
                    n_reads = mode_count // MAX_COUNT_HR + 1

                    for nn in range(n_reads):
                        resp = await func(
                            nn * MAX_COUNT_HR,
                            count=MAX_COUNT_HR,
                            slave=self.slave,
                        )

                        if resp.isError():
                            raise ValueError(
                                f"Invalid response for block {mode!r}: "
                                f"0x{resp.function_code:02X}."
                            )

                        data += resp.registers

                for name, register in self.items():
                    if register.mode != mode:
                        continue

                    value = data[register.address : register.address + register.count]

                    # Apply any overrides from the configuration.
                    if name in self.overrides:
                        value = self.overrides[name]

                    value = register.decode(value)

                    if isinstance(value, Sequence) and len(value) == 1:
                        value = value[0]

                    self.register_cache[name] = value

        registers = self.register_cache.freeze()

        # Just to double check that none of the values have expired, we loop over the
        # dictionary and if necessary we read the register again.
        for name, value in registers.items():
            if value is None:
                registers[name] = await self[name].read(use_cache=False)

        return registers

    async def read_group(self, group: str, use_cache: bool = True):
        """Returns a dictionary of all read registers that match a ``group``."""

        registers = await self.read_all(use_cache=use_cache)

        group_registers: dict[str, int | bool] = {}
        for name in self:
            register = self[name]
            if register.group is not None and register.group == group:
                if name not in registers:
                    continue

                group_registers[name] = registers[name]

        return group_registers

    async def read_register(self, register: str, use_cache: bool = True) -> int | bool:
        """Reads a register."""

        if register not in self:
            raise ValueError(f"Register {register!r} not found.")

        return await self[register].read(use_cache=use_cache)

    async def write_register(self, register: str, value: int | bool):
        """Writes a value to a register."""

        assert isinstance(register, str)

        if register not in self:
            raise ValueError(f"Register {register!r} not found.")

        await self[register].write(value)
