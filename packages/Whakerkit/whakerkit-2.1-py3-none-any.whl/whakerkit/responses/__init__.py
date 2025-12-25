# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.responses.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The responses for all known pages.

Copyright (C) 2024-2025 Brigitte Bigi, CNRS
Laboratoire Parole et Langage, Aix-en-Provence, France

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This banner notice must not be removed.

"""

from .base import set_base_response_class
from .base_auth_resp import WhakerkitAuthResponse
from .pages_resp import WhakerKitResponse
from .deposit_resp import DepositResponse
from .docs_resp import DocsResponse
from .stats_resp import StatsResponse

# ---------------------------------------------------------------------------
# ⚠️ IMPORTANT ⚠️
#
# Do not import classes that inherit from WhakerKitResponse here.
# This includes, for example: DocsResponse, StatsResponse, etc.
#
# The base response system (via set_base_response_class) must be configured
# BEFORE importing these classes.
# Otherwise, they will inherit from the wrong base class.
#
# ==> These classes should only be imported *after* calling
#     set_base_response_class() in the files where they are used.
# ---------------------------------------------------------------------------

__all__ = (
    "set_base_response_class",
    "WhakerKitResponse",
    "WhakerkitAuthResponse",
    "DepositResponse",
    "DocsResponse",
    "StatsResponse"
)
