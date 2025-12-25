# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.head_node.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Head node of each page

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

import logging

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import HTMLHeadNode

import whakerkit
from whakerkit.components import Components

# ---------------------------------------------------------------------------


CSS_MIME_TYPE = "text/css"
JS_MIME_TYPE = "application/javascript"

# ---------------------------------------------------------------------------


SUBMIT_BTN_SCRIPT = """
window.Wexa.onload.addLoadFunction(() => {
    const submit_button = document.querySelector('button[type="submit"]');
    if (submit_button == null) {
        return null;
    }

    submit_button.onclick = () => {
        const form = document.getElementsByTagName("form")[0];
        if (form != null) {
            const url = window.Wexa.accessibility.set_url_with_parameters(form.action);
            form.action = url;
        }
    }
});
"""

# ---------------------------------------------------------------------------


class WhakerKitHeadNode(HTMLHeadNode):
    """Node for the head of each page.

    """

    def __init__(self, parent, title: str = "WhakerKit"):
        """Create the head node.

        """
        self._components_activated = list()

        super(WhakerKitHeadNode, self).__init__(parent)
        self.reset(title)

    # -----------------------------------------------------------------------

    def reset(self, title: str):
        """Reset the head to its default values.

        :param title: The title of the page to be added into the head.

        """
        # Delete the existing list of children
        self.clear_children()

        # The default meta tags
        self.meta({"charset": "utf-8"})
        self.meta({"http-equiv": "X-UA-Compatible", "content": "IE=edge"})
        self.meta({"name": "keywords",
                   "content": "WhakerKit, WhakerPy, Whakerexa, Brigitte, Bigi, CNRS"})
        self.meta({"name": "viewport",
                   "content": "width=device-width, initial-scale=1.0, user-scalable=yes"})

        # Add the given title
        title_node = HTMLNode(self.identifier, "title", "title", value=title)
        self.append_child(title_node)

        # Add the CSS style, from Whakerexa
        self.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/wexa.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/layout.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/button.css", link_type=CSS_MIME_TYPE)
        self.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/menu.css", link_type=CSS_MIME_TYPE)
        # Add the custom CSS style
        self.link(rel="stylesheet", href=whakerkit.sg.path + "statics/css/whakerkit.css",
                  link_type=CSS_MIME_TYPE)

        # Add the javascript, from Whakerexa
        self.script(src=whakerkit.sg.whakerexa + "js/wexa.js", script_type="module")

        # Add the javascript with utility functions
        self.append_child(HTMLNode(self.identifier, None, "script",
                                   value=SUBMIT_BTN_SCRIPT,
                                   attributes={'type': "module"}))

    # ---------------------------------------------------------------------------
    # PUBLIC METHODS
    # ---------------------------------------------------------------------------

    def enable_component(self, component_name: str) -> bool:
        """Enable styles and scripts for the specified component.

        :param component_name: (str) Name of the component to enable.

        """
        # retrieve required files for this component (raises KeyError if unknown)
        try:
            files = Components.get(component_name)
        except KeyError:
            logging.warning(f"Component '{component_name}' is not registered.")
            return False

        # avoid double‐enabling
        if component_name not in self._components_activated:
            # import each required file
            for file in files:
                if file.endswith(".css"):
                    self.link(rel="stylesheet",
                              href=whakerkit.sg.whakerexa + "css/" + file,
                              link_type=CSS_MIME_TYPE)
                elif file.endswith(".js"):
                    self.script(whakerkit.sg.whakerexa + "js/" + file,
                                script_type=JS_MIME_TYPE)
                else:
                    logging.warning(f"Unknown required file '{file}' for component '{component_name}'")

            # mark as activated
            self._components_activated.append(component_name)
        else:
            logging.debug(f"The component '{component_name}' is already enabled.")

        return True
