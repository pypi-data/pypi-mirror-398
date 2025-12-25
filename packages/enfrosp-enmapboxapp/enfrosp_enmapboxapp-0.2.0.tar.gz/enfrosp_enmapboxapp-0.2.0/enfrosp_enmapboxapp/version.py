# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
# FileType: SOURCE
# FileCopyrightText: 2025, GFZ Helmholtz Centre for Geosciences
# FileCopyrightText: 2025, Daniel Scheffler (danschef@gfz.de)

"""Version module for EnFROSP EnMAP-Box-App."""

__version__ = "0.2.0"
__versionalias__ = "2025-12-22_01"
__author__ = 'Daniel Scheffler'

_minimal_enfrosp_version = '0.3.1'


def check_minimal_enfrosp_version(enfrosp_version: str):
    from packaging.version import parse as _parse_version
    if _parse_version(enfrosp_version) < _parse_version(_minimal_enfrosp_version):
        raise EnvironmentError(f"The installed version of EnFROSP (v{enfrosp_version}) is too old. "
                               f"At least version {_minimal_enfrosp_version} is required.")
