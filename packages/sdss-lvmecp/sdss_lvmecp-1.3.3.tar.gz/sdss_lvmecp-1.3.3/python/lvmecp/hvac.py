#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-09-14
# @Filename: hvac.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

from lvmecp.module import PLCModule


__all__ = ["HVACController"]


class HVACController(PLCModule):
    """Monitors the HVAC system."""

    flag = None
    interval = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.status: dict[str, int | bool] = {}

    async def _update_internal(self, **kwargs):
        """Update status."""

        self.status = await self.modbus.read_all()
