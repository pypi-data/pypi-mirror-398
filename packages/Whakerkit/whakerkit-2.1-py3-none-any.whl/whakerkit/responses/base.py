"""
:filename: whakerkit.responses.base.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class for a WhakerKitResponse or a Custom inherited one.

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

from __future__ import annotations

import logging

from .pages_resp import WhakerKitResponse

# -----------------------------------------------------------------------------
# Configurable Base Class Registry
# -----------------------------------------------------------------------------
# This module provides a simple and clean way to allow the response library
# to override the default base class used across the components.
#
# Usage:
#   1. Define a default base class in the library (e.g., `WhakerKitResponse`).
#   2. Let users optionally define their own subclass and register it using
#      `set_base_response_class()`.
#   3. All other components can retrieve the currently configured base class
#      using `get_base_response_class()` and subclass it.
#
# This pattern is useful :
# - to allow extension/customization without changing core logic.
# - to offer a default implementation, but make it swappable.
# - to have multiple components relying on the same customizable base.
# -----------------------------------------------------------------------------

# Holds the user-defined base class, or None if not configured.
_base_response_class = None

# ---------------------------------------------------------------------------


def set_base_response_class(cls: WhakerKitResponse, validate: bool = True):
    """Set the base response class to be used by all components that rely on it.

    This function should be called by the user **before** any component
    relying on the base class is instantiated.

    :param cls: (WhakerKitResponse) The custom class to be used as the base
        response class. It should inherit from the default class (e.g.,
        WhakerKitResponse) to ensure compatibility.
    :param validate: (bool) Whether to check type of the given response class, or not.
    :raises: TypeError: Invalid given response class.

    :example:
    >>> from whakerkit import set_base_response_class
    >>> from my_custom_module import MyCustomResponse
    >>> set_base_response_class(MyCustomResponse)

    """
    if validate:
        # Try duck-typing: Check for a required method or attribute
        if not hasattr(cls, "set_pagename"):
            raise TypeError("set_base_response_class: The given custom base class "
                            "is not an instance or inheritance of WhakerKitResponse.")
    global _base_response_class
    _base_response_class = cls
    logging.debug(f"Response system is {str(_base_response_class)}")

# ---------------------------------------------------------------------------


def get_base_response_class() -> type | None:
    """Get the currently configured base response class.

    Return the custom base class if it was set via `set_base_response_class()`,
    otherwise the default `WhakerKitResponse` defined in the library.

    - This function will dynamically import the default class to avoid
      circular import issues.
    - The default class import path should be adjusted based on your project.

    :return: (type) The base response class.

    """
    if _base_response_class is not None:
        return _base_response_class

    # Default fallback import — adjust this to your actual module path
    return WhakerKitResponse
