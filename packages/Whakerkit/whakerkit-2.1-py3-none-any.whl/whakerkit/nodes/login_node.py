# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.login_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for the user login dialog

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

from whakerpy import HTMLNode

import whakerkit
from whakerkit import get_msg

from .accessibility import WhakerKitAccessibilityNavNode
from .utils import create_action_button

# ---------------------------------------------------------------------------


MSG_HEADER_H1 = "Login"
MSG_USERNAME = "Username"
MSG_USERID = "Login ID"
MSG_PASSWORD = "Password"
MSG_LOGIN = "Log in"

# ---------------------------------------------------------------------------


class WhakerKitLoginNode(HTMLNode):
    """Node for the login dialog.

    """

    def __init__(self, parent: str):
        """Create the login node.

        :param parent: (str) The parent node identifier

        """
        super(WhakerKitLoginNode, self).__init__(parent, "login_dialog", "dialog",
                                                 attributes={"id": "login_dialog"})
        self.reset()

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset the login to its default values.

        Expects a JS instance authManager to open the login dialog.

        """
        self._children = list()

        # Color & Scheme buttons -- for accessibility
        nav = WhakerKitAccessibilityNavNode(self.identifier)
        self.append_child(nav)
        # Welcome message -- title
        title = HTMLNode(self.identifier, None, "h1", value=get_msg(MSG_HEADER_H1))
        self.append_child(title)

        # Login content
        attributes = {
            "method": "POST",
            "id": "login_form",
            "accept-charset": "UTF-8",
            "action": "javascript:void(0);",
            "onsubmit": "authManager.submitLoginDialog();"
        }
        form = HTMLNode(self.identifier, "login_form", "form", attributes=attributes)
        self.append_child(form)
        WhakerKitLoginNode.__login_form_content(form)

    # -----------------------------------------------------------------------

    @staticmethod
    def __login_form_content(form: HTMLNode):
        """Create the content of the login form.

        :param form: (HTMLNode) The node of the login form

        """
        # Username
        label_username = HTMLNode(form.identifier, "username_label", "label",
                                  value=get_msg(MSG_USERNAME), attributes={"for": "username_input"})
        form.append_child(label_username)
        att = {
            "id": "username_input",
            "name": "username_input",
            "placeholder": get_msg(MSG_USERID),
            "type": "text",
            "aria-labelledby": "username_label"
        }
        input_username = HTMLNode(form.identifier, "username_input", "input", attributes=att)
        form.append_child(input_username)

        # Password
        label_password = HTMLNode(form.identifier, "password_label", "label",
                                  value=get_msg(MSG_PASSWORD), attributes={"for": "password_input"})
        form.append_child(label_password)
        att = {
            "id": "password_input",
            "name": "password_input",
            "placeholder": "*********",
            "type": "password",
            "aria-labelledby": "password_label"
        }
        input_password = HTMLNode(form.identifier, "password_input", "input", attributes=att)
        form.append_child(input_password)

        # Submit button
        btn = create_action_button(form.identifier, None, get_msg(MSG_LOGIN),
                                   whakerkit.sg.path + "statics/icons/authentication.png")
        btn.add_attribute("id", "login_button")
        btn.add_attribute("type", "submit")
        form.append_child(btn)
