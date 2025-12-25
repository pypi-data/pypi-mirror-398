# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.accessibility.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for the accessibility buttons

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

import whakerkit
from whakerkit import get_msg

# ---------------------------------------------------------------------------


MSG_ALT_CONTRAST = "Contrast"
MSG_ALT_THEME = "Color scheme"

# ---------------------------------------------------------------------------


class WhakerKitAccessibilityNavNode(HTMLNode):
    """Node for the accessibility nav of the website.

    """

    def __init__(self, parent: str):
        """Create the 'nav' node.

        :param parent: (str) The parent identifier node

        """
        super(WhakerKitAccessibilityNavNode, self).__init__(parent, "accessibility_nav", "nav")
        self.reset()

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset the header to its default values."""
        self.clear_children()

        # Contrast Button
        button_contrast = HTMLNode(self.identifier, None, "button",
                                   attributes={
                                       "role": "menuitem",
                                       "onclick": "window.Wexa.accessibility.switch_contrast_scheme();",
                                       "id": "btn-contrast"}
                                   )
        self.append_child(button_contrast)
        img_contrast = HTMLNode(button_contrast.identifier, None, "img",
                                attributes={"src": whakerkit.sg.whakerexa + "icons/contrast_switcher.jpg",
                                            "alt": get_msg(MSG_ALT_CONTRAST),
                                            "id": "img-contrast"})
        button_contrast.append_child(img_contrast)

        # Color Theme Button
        button_theme = HTMLNode(self.identifier, None, "button",
                                attributes={"role": "menuitem",
                                            "onclick": "window.Wexa.accessibility.switch_color_scheme();",
                                            "id": "btn-theme"})
        self.append_child(button_theme)
        img_theme = HTMLNode(button_theme.identifier, None, "img",
                             attributes={"src": whakerkit.sg.whakerexa + "icons/theme_switcher.png",
                                         "alt": get_msg(MSG_ALT_THEME),
                                         "id": "img-theme"})
        button_theme.append_child(img_theme)

# ---------------------------------------------------------------------------
class AccessibilityButton(HTMLNode):
    """To be used."""

    def __init__(self, parent_id: str, name: str):
        super().__init__(parent_id, f"accessibility-{name}-button", "button", attributes={
            'id': f"{name}-switch-button",
            'class': "print-off",
            'onclick': f"window.Wexa.accessibility.switch_{name}_scheme()",
            'role': "menuitem",
            'aria-label': f"Change {name}"
        })

        self.append_child(HTMLNode(self.identifier, None, "img", attributes={
            'id': f"img-{name}",
            'class': "nav-item-img",
            'src': whakerkit.sg.whakerexa + f"icons/{name}_switcher.png",
            'alt': f"{name} switch button"
        }))

