# -*- coding: UTF-8 -*-
"""
:filename: responses.pages_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system for any page of the website.

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

import os
import codecs
import logging

from whakerpy.htmlmaker import HTMLNode
from whakerpy.httpd import BaseResponseRecipe

import whakerkit
from whakerkit.nodes import WhakerKitHeadNode
from whakerkit.nodes import WhakerKitNavNode
from whakerkit.nodes import WhakerKitHeaderNode
from whakerkit.nodes import WhakerKitFooterNode

# ---------------------------------------------------------------------------


class WhakerKitResponse(BaseResponseRecipe):
    """Create a Response system for dynamic pages.

    The page can or cannot have a static body->main content.

    """
    _name = ""

    def __init__(self,
                 name: str | None = None,
                 tree: HTMLNode | None = None,
                 title: str = whakerkit.sg.name):
        """Create a HTTPD Response instance with a default response.

        :param name: (str) Filename of the body main content.

        """
        self._title = title
        self._name = name
        if name is not None:
            self._page_name = os.path.basename(name)
        else:
            name = "undefined"
            self._page_name = ""

        # Inheritance with a given dynamic HTMLTree.
        super(WhakerKitResponse, self).__init__(name, tree)

        self._unittest_files = list()

    # ---------------------------------------------------------------------------
    # PUBLIC STATIC METHODS
    # ---------------------------------------------------------------------------

    @classmethod
    def page(cls):
        """Return the current HTML body->main filename or an empty string."""
        return cls._name

    # -----------------------------------------------------------------------

    def get_pagename(self) -> str:
        """Return the name of the HTML page as seen in the URL."""
        return self._page_name

    # -----------------------------------------------------------------------

    def set_pagename(self, page_name: str):
        """Set the name of this page as seen in the url.

        :param page_name: (str) Name of the HTML page.

        """
        self._page_name = page_name
        # Update current nav page
        self._htree.body_nav.set_nav_current(page_name)

    # -----------------------------------------------------------------------
    # Construct the tree
    # -----------------------------------------------------------------------

    def create(self):
        """To be overridden. Create the page tree.

        Create the head and body_nav of the dynamic tree.

        """
        self._htree.head = WhakerKitHeadNode(self._htree.identifier, title=self._title)
        self._htree.body_main.set_attribute("id", "main-content")
        self._htree.body_nav = WhakerKitNavNode(self._htree.identifier)

        # If the page_name is already defined
        if len(self._page_name) > 0:
            self._htree.body_nav.set_nav_current(self._page_name)

    # -----------------------------------------------------------------------

    def create_tree_header(self, header_filename: str | None = None):
        """Create the body_header of the dynamic tree."""
        self._htree.body_header = WhakerKitHeaderNode(
            self._htree.identifier,
            header_filename
        )

    # -----------------------------------------------------------------------

    def create_tree_footer(self, footer_filename: str | None = None):
        """Create the body_footer of the dynamic tree."""
        self._htree.body_footer = WhakerKitFooterNode(
            self._htree.identifier,
            footer_filename
        )

    # ---------------------------------------------------------------------------

    def enable_components(self, components: list) -> None:
        """Wrapper of the enable_component method in the head.

        :param components: (list) List of component names

        """
        for component in components:
            if hasattr(self._htree.head, "enable_component") \
                    and callable(self._htree.head.enable_component):
                self._htree.head.enable_component(component)
            else:
                logging.warning(f"Components {component} are not enabled: "
                                f"the head node does not implement this.")

    # ---------------------------------------------------------------------------

    def enable_unittests(self) -> None:
        """Import unit test files append before in the html head.

        """
        serialize_head = self._htree.head.serialize()

        if "UnitTest.js" not in serialize_head:
            self._htree.add_script_file(whakerkit.sg.whakerexa + "js/tests/UnitTest.js")

        for file_path in self._unittest_files:
            if os.path.basename(file_path) not in serialize_head:
                self._htree.add_script_file(file_path)

    # ---------------------------------------------------------------------------
    # SETTERS
    # ---------------------------------------------------------------------------

    def add_unittest_file(self, file_path: str) -> None:
        """Add a new unit test file to the list.

        If you want to use this files when the webapp starts, call the
        'enable_unit_tests' method.

        :param file_path: The path of the unit test file to add
        :raises: FileNotFoundError: If the given file path doesn't exist

        """
        if os.path.exists(file_path):
            self._unittest_files.append(file_path)
        else:
            raise FileNotFoundError(f"The given file: {file_path} doesn't exist!")

    # -----------------------------------------------------------------------
    # Override WhakerPy private methods
    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :param kwargs: (dict) the keyword arguments
        :return: (bool) True if the whole page must be baked, False otherwise.

        """
        self._status.code = 200
        return True

    # -----------------------------------------------------------------------

    def _invalidate(self):
        """Override. Remove children nodes of the body->main."""
        self._htree.body_main.clear_children()

    # -----------------------------------------------------------------------

    def _bake(self):
        """Create the dynamic content of body->main.

        Load the content from a file.

        """
        if self._name is not None and self._name != "Undefined":
            # Define this page main content, from a static HTML content
            # located at the root of the project
            filename = whakerkit.sg.get_root_path() + "/" + self._name
            if os.path.exists(filename) is True and os.path.isfile(filename) is True:
                with codecs.open(filename, "r", "utf-8") as fp:
                    lines = fp.readlines()
                    self._htree.body_main.set_value(" ".join(lines))
            else:
                self._status.code = 404
