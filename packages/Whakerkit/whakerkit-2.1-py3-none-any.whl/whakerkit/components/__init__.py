# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.components.__init__.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Registry for component classes.

This file is part of WhakerKit: https://whakerkit.sourceforge.io
This file was originally part of SPPAS - by Brigitte Bigi, CNRS.
Integrated into WhakerKit 1.2.

Copyright (C) 2021-2025 Brigitte Bigi, CNRS
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
from types import MappingProxyType

from .card import CardNode
from .book import BookNode
from .video_popup import VideoPopupNode

# ---------------------------------------------------------------------------


class Components:
    """Registry for component classes.

    - _original_registry: Immutable mapping of built-in components.
    - _dynamic_registry: Mutable mapping for custom extensions.

    This registry is global and shared across all imports. To extend components,
    ensure that the module registering custom components (e.g., components_extend)
    is imported **before** any calls to get() or all(), so that register() runs in time.

    :example:
    >>> from whakerkit import Components
    >>> # Add a component to the registry
    >>> Components.register('MyWidget', MyWidgetNode.REQUIRED)
    >>> widget = Components.get('MyWidget')
    >>> for name, comp in Components.all().items():
    >>>     print(name, comp)

    """

    # Immutable mapping of the three core components.
    _original_registry: MappingProxyType = MappingProxyType({
        'Card': CardNode.REQUIRED,
        'Book': BookNode.REQUIRED,
        'VideoPopup': VideoPopupNode.REQUIRED,
        'Dialog': ("dialog.css", )
    })

    # Mutable mapping for user-defined or extended components.
    _dynamic_registry: dict = {}

    # -----------------------------------------------------------------------

    @classmethod
    def register(cls, name: str, component) -> None:
        """Register a new component under the given name.

        :param name: (str) The name of the component.
        :param component: (any) The component to register.
        :raises: KeyError: If attempting to override an original component.

        """
        if name in cls._original_registry:
            raise KeyError(f"Component '{name}' is protected and cannot be overridden.")

        cls._dynamic_registry[name] = component

    # -----------------------------------------------------------------------

    @classmethod
    def get(cls, name: str):
        """Retrieve a component by name.

        :return: (any) The original component if name is in the original registry,
            otherwise the user-registered component.

        """
        if name in cls._original_registry:
            return cls._original_registry[name]

        return cls._dynamic_registry[name]

    # -----------------------------------------------------------------------

    @classmethod
    def all(cls) -> dict:
        """Return a merged view of original and user-registered components.

        :return: (dict) A new dict combining original and dynamic registries.

        """
        merged = dict(cls._original_registry)
        merged.update(cls._dynamic_registry)
        return merged
