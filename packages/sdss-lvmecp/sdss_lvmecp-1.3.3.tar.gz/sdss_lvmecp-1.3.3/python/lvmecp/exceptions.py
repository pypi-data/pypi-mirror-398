#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-05-23
# @Filename: exceptions.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations


class ECPError(Exception):
    """A general ``lvmecp`` error."""

    pass


class DomeError(ECPError):
    """A dome-related error."""

    pass


class SafetyError(ECPError):
    """A safety-related error."""

    pass


class ECPWarning(UserWarning):
    """General warnings for ``lvmecp.``"""

    pass
