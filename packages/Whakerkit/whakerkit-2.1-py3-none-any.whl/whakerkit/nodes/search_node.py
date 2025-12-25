"""
:filename: whakerkit.nodes.search_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A node to search keywords into the documents -- not implemented

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

from ..documents import DocumentsManager

# ---------------------------------------------------------------------------


MSG_TITLE_KEYWORDS = "Mots-clés"
MSG_TITLE_SEARCH = "Le document contient les mots : "
MSG_DO_SEARCH = "Lancer la recherche"

# ---------------------------------------------------------------------------


class WhakerKitSearchNode(HTMLNode):
    """Find documents matching keywords.

    """

    def __init__(self, parent):
        """Create the search node.

        :param parent: (HTMLNode) The parent node

        """
        super(WhakerKitSearchNode, self).__init__(parent, None, "fieldset", attributes={"class": "width-full"})

        # Add table for search
        # ---------------------
        table = HTMLNode(self.identifier, None, "table", attributes={"role": "presentation"})
        self.append_child(table)

        # Search bar
        tbody_filename = HTMLNode(table.identifier, None, "tbody")
        table.append_child(tbody_filename)
        tr = HTMLNode(tbody_filename.identifier, None, "tr")
        tbody_filename.append_child(tr)
        td = HTMLNode(tr.identifier, None, "td", attributes={"class": "width_30"})
        tr.append_child(td)
        bold = HTMLNode(td.identifier, None, "b", value=MSG_TITLE_SEARCH)
        td.append_child(bold)
        td = HTMLNode(tr.identifier, None, "td")
        tr.append_child(td)
        input_search = HTMLNode(td.identifier, None, "input",
                                attributes={
                                    "class": "flex-item", "id": "site-search",
                                    "type": "text", "name": "search",
                                    "placeholder": "Mots à chercher",
                                    "aria-label": "Mots à chercher",
                                    "disabled": "disabled"})
        td.append_child(input_search)

        # Submit button
        # -------------
        button_submit = HTMLNode(self.identifier, None, "button",
                                 attributes={
                                     "class": "center flex-panel",
                                     "type": "submit",
                                     "id": "site_search_button",
                                     "disabled": "disabled"},
                                 value=MSG_DO_SEARCH)
        img_search = HTMLNode(button_submit.identifier, None, "img",
                              attributes={"class": "small-logo", "src": whakerkit.sg.path + "statics/icons/search.png",
                                          "alt": "Recherche"})
        button_submit.append_child(img_search)
        self.append_child(button_submit)

    # -----------------------------------------------------------------------

    def get_filetype(self):
        """Get all file types.

        :return: (list) File types

        """
        filetypes = []
        doc = DocumentsManager(whakerkit.sg.uploads)
        doc.collect_docs()
        for docs in self.__docs.get_docs_sorted_by_newest():
            filetypes.append(docs.filetype)

        return filetypes

    # -----------------------------------------------------------------------

    def get_all_authors(self):
        """Get all authors.

        :return: (list) Authors

        """
        authors = []
        for docs in self.__docs.get_docs_sorted_by_newest():
            authors.append(docs.author)

        return authors
