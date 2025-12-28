#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-05-24
# @Filename: maskbits.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import enum


__all__ = ["DomeStatus", "LightStatus", "SafetyStatus"]


class Maskbit(enum.Flag):
    """A maskbit enumeration. Intended for subclassing."""

    __version__ = None
    __unknown__ = 0x100000

    def __str__(self):
        enabled = [
            bit.name
            for bit in self.__class__
            if bit.value & self.value and bit.name is not None
        ]
        return ",".join(enabled)

    @property
    def version(self):
        """The version of the flags."""

        return self.__version__

    @property
    def active_bits(self):
        """Returns a list of flags that match the value."""

        return [bit for bit in self.__class__ if bit.value & self.value]


class SafetyStatus(Maskbit):
    """Safety and emergency status."""

    __version__ = "1.0.0"

    LOCAL = 0x1
    DOOR_CLOSED = 0x2
    DOOR_LOCKED = 0x4
    O2_SENSOR_UR_ALARM = 0x100  # Utilities room
    O2_SENSOR_UR_FAULT = 0x200
    O2_SENSOR_SR_ALARM = 0x400  # Spec room
    O2_SENSOR_SR_FAULT = 0x800
    RAIN_SENSOR_ALARM = 0x1000
    E_STOP = 0x2000
    DOME_LOCKED = 0x4000
    DOME_ERROR = 0x8000
    E_STOP_LN2 = 0x10000
    UNKNOWN = 0x100000


class DomeStatus(Maskbit):
    """Position and status of the dome."""

    __version__ = "1.0.0"

    OPEN = 0x1
    CLOSED = 0x2
    MOVING = 0x4
    POSITION_UNKNOWN = 0x10
    DRIVE_ENABLED = 0x20
    MOTOR_CLOSING = 0x40
    MOTOR_OPENING = 0x80
    BRAKE_ENABLED = 0x100
    NE_LIMIT = 0x200
    NW_LIMIT = 0x400
    SE_LIMIT = 0x800
    SW_LIMIT = 0x1000
    OVERCURRENT = 0x2000
    DRIVE_ERROR = 0x4000
    DRIVE_AVAILABLE = 0x8000
    NODRIVE = 0x10000
    UNKNOWN = 0x100000


class LightStatus(Maskbit):
    """Lights status. Active bits indicate on lamps."""

    __version__ = "1.0.0"

    CONTROL_ROOM = 0x1
    UTILITIES_ROOM = 0x2
    SPECTROGRAPH_ROOM = 0x4
    UMA_ROOM = 0x8
    TELESCOPE_BRIGHT = 0x10
    TELESCOPE_RED = 0x20
    UNKNOWN = 0x100000
