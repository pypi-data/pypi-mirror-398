# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.nav_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for the navigation menu

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

import os

from whakerpy.htmlmaker import HTMLNavNode

# ---------------------------------------------------------------------------


class WhakerKitNavNode(HTMLNavNode):
    """Class to represent the nav node of any page of the website.

    """

    def __init__(self, parent):
        """Create the nav node."""
        super(WhakerKitNavNode, self).__init__(parent)
        self._nav_items = list()
        self.reset()
        self.set_attribute("id", "nav-content")

    # -----------------------------------------------------------------------

    def set_nav_current(self, page_name: str) -> None:
        """Set the current nav item. Do not cancel any previous one.

        :param page_name: (str) Name of the new current html page.

        """
        if isinstance(page_name, str) is False or len(page_name) == 0:
            return

        filename, _ = os.path.splitext(page_name)
        if "_" in filename:
            filename = filename[:filename.index("_")+2]

        for item in self._nav_items:
            if item.has_attribute("href"):
                value = item.get_attribute_value("href")
                if value.startswith(filename) is True:
                    item.add_attribute("class", "nav-current")
                    break

    # -----------------------------------------------------------------------

    def reset(self) -> None:
        """To be overridden. Reset the nav to its default values.

        """
        # Delete the existing list of children
        self._nav_items = list()
