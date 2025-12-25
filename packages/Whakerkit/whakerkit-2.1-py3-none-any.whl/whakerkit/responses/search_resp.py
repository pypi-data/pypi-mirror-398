# -*- coding: UTF-8 -*-
"""
:filename: responses.search_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system to search for documents -- not implemented

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

import whakerkit

from ..uploads_manager import WhakerKitDocsManager
from ..nodes.search_node import WhakerKitSearchNode

from .base import get_base_response_class  # WhakerKitResponse or Custom

# ---------------------------------------------------------------------------

# script for submit buttons allowing to keep accessibility parameters in the
# url (color and contrast)
JS_SCRIPT = """
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

MSG_TITLE_SEARCH = "Recherche de documents"

# ---------------------------------------------------------------------------


class SearchResponse(get_base_response_class()):
    """The bake system for the search page.

    This response is under-construction. It aims at implementing a search
    bar to retrieve document from keywords.

    """

    def __init__(self):
        """Create the response for the index page.

        The body->main of this page is created fully dynamically, there's no
        file to get content from.

        """
        super(SearchResponse, self).__init__(name=None, title=MSG_TITLE_SEARCH)
        # Collect all stored documents: allows to know the N most recent and
        # the N most viewed.
        self.__doc_manager = WhakerKitDocsManager()
        self.__doc_manager.collect_docs(mutable=False)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process a posted event from the client.

        :param events: (dict) the posted events
        :param kwargs: (dict) the keyword arguments
        :return: (bool) True to bake the page

        """
        # HTTP status
        self._status.code = 200
        # Received events
        if "event_name" in events:
            if events["event_name"] == "search":
                pass
        # Must bake the page
        return True

    # -----------------------------------------------------------------------

    def create(self):
        """Override. Create the page tree.

        Set page name and add required js in the tree->head.

        """
        get_base_response_class().create(self)
        self.set_pagename("search.html")

        js = "text/javascript"
        self._htree.head.script(whakerkit.sg.path + "statics/js/doc_download.js", js)

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Create the dynamic content in the body->main of the page.

        """
        # Page main title -- <h1> element
        h1 = self._htree.element("h1")
        h1.set_value(MSG_TITLE_SEARCH)

        # Search. To be implemented.
        search = WhakerKitSearchNode(self._htree.body_main.identifier)
        self._htree.body_main.append_child(search)
