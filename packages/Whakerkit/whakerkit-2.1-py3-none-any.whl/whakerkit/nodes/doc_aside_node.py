# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.doc_aside_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for the aside file

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
along with this program. If not, see <https://www.gnu.org/licenses/>.

This banner notice must not be removed.

"""

from whakerpy import HTMLNode

from whakerkit import get_msg

# ---------------------------------------------------------------------------

MSG_DETAILS = "Information"
MSG_CLOSE = "Close"
MSG_DOC_FILENAME = "Name: "
MSG_DOC_AUTHOR = "Author: "
MSG_DOC_FILETYPE = "Type: "
MSG_DOC_DATE = "Added on: "
MSG_DOC_DESCRIPTION = "Description: "
MSG_DOC_DOWNLOADS = "Downloads: "
MSG_DOC_DOWNLOADS_VALUE = "0"

# ---------------------------------------------------------------------------


class WhakerKitDocAsideNode(HTMLNode):
    """The node of the aside element.

    The aside content is used to display all the information on a document.

    """

    def __init__(self, parent: str):
        """Create the node.

        :param parent: (str) The parent node identifier

        """
        super(WhakerKitDocAsideNode, self).__init__(
            parent,
            "doc_aside",
            "aside",
            attributes={"id": "doc_aside", "class": "doc-aside", "tabindex": "0"})
        self.reset()

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset the aside node to its default values."""
        h2 = HTMLNode(self.identifier, "h2", "h2")
        h2.set_value(get_msg(MSG_DETAILS))
        self.append_child(h2)

        self.__append_p("doc_filename", value=get_msg(MSG_DOC_FILENAME))
        self.__append_p("doc_author", value=get_msg(MSG_DOC_AUTHOR))
        self.__append_p("doc_filetype", value=get_msg(MSG_DOC_FILETYPE))
        self.__append_p("doc_date", value=get_msg(MSG_DOC_DATE))
        self.__append_p("doc_description", value=get_msg(MSG_DOC_DESCRIPTION))
        self.__append_p("doc_downloads", value=get_msg(MSG_DOC_DOWNLOADS), span_value=get_msg(MSG_DOC_DOWNLOADS_VALUE))

        button = HTMLNode(self.identifier, "button", "button",
                          attributes={"id": "close_aside_button", "onclick": "asideManager.closeDetails()",
                                      "class": "apply-button"})
        button.set_value(get_msg(MSG_CLOSE))
        self.append_child(button)

    # -----------------------------------------------------------------------

    def __append_p(self, name: str, value="", span_value="--"):
        """Append a paragraph with given identifier name.

        :param name: (str) Identifier for the paragraph.

        """
        p = HTMLNode(self.identifier, name + "_p", "p", value="<b>"+value+"</b>")
        self.append_child(p)
        name = name + "_span"
        span = HTMLNode(p.identifier, "span", "span",
                        attributes={"id": name},
                        value=span_value)
        p.append_child(span)
