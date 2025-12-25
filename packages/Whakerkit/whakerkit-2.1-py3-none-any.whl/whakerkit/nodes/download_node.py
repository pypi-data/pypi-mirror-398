# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.download_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for the link to a document.

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

from whakerpy.htmlmaker import HTMLNode

import whakerkit

# ---------------------------------------------------------------------------


class WhakerKitDownloadNode(HTMLNode):
    """Node for a link to a document.

    Expects a JS instance docManager to increment the number of downloads.

    """
    def __init__(self, parent: str, href, folder_name: str, text: str = ""):
        """Create the 'a' node.

        :param parent: (str) The parent node identifier
        :param href: (str) relative path to the file to be downloaded
        :param folder_name: (str) identifier of the document
        :param text: (str) text to be displayed

        """
        super(WhakerKitDownloadNode, self).__init__(parent, None, "button")
        self.add_attribute("onclick", f"docManager.incrementDownloads('{href}', '{folder_name}');")
        img = HTMLNode(self.identifier, None, "img")
        img.add_attribute("src", whakerkit.sg.path + "statics/icons/download.png")
        img.add_attribute("alt", "")
        self.append_child(img)
        if len(text) > 0:
            span = HTMLNode(self.identifier, None, "span", value=text)
            self.append_child(span)
