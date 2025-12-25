# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.utils.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Utilities for creating nodes

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

from whakerpy.htmlmaker import HTMLNode


def create_action_button(parent_id, onclick, msg, icon):
    """Return an HTMLNode representing a button.

    Example of such serialized button:
        <button class="flex-item action-button" onclick="docManager.filterDocuments();">
            <img class="small-logo" src="./whakerkit/statics/icons/filter.png" alt=""></img>
            <span> Filtrer les documents </span>
        </button>

    """
    btn = HTMLNode(parent_id, None, "button", attributes={"class": "flex-item action-button"})
    if onclick is not None:
        btn.add_attribute("onclick", onclick)
        btn.add_attribute("onkeydown", onclick)
    img = HTMLNode(btn.identifier, None, "img", attributes={"class": "small-logo", "src": icon, "alt": ""})
    btn.append_child(img)
    span = HTMLNode(btn.identifier, None, "span", value=msg)
    btn.append_child(span)
    return btn
