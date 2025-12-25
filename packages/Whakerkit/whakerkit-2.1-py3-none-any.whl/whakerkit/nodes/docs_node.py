# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.docs_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: HTMLNode for any list of documents

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
import logging

from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg
from ..uploads_manager import WhakerKitDocsManager

from .download_node import WhakerKitDownloadNode
from .doc import DOC_FIELDS

# ---------------------------------------------------------------------------


MSG_ACTION_DETAILS = "Details"
MSG_ACTION_DESCRIBE = "Describe"
MSG_DOWNLOAD = "Download"
MSG_APPLY = "Apply"
MSG_ACTION_DELETE = "Delete"
MSG_ACTIONS = "Actions"
MSG_VISIBILITY = "Column visibility"

# ---------------------------------------------------------------------------


class ToggleColumnsNode(HTMLNode):
    """A node to select which columns of the DocumentsNode is displayed.

    Requires a global JS "docManager" which is an instance of "DocumentsManager()".

    """

    def __init__(self, parent: str):
        """Create the node instance.

        :param parent: (str) The parent node identifier

        """
        super(ToggleColumnsNode, self).__init__(parent, "toggleselect_div", "div")

        details = HTMLNode(self.identifier, "toggable_details", "details")
        details.add_attribute("id", "toggable_details")
        self.append_child(details)
        self.__add_summary(details)
        self.__add_main(details)

        button = HTMLNode(self.identifier, None, "button", value=get_msg(MSG_APPLY))
        button.add_attribute("class", "apply-button")
        button.add_attribute("onclick", "docManager.updateColumns();")
        self.append_child(button)

    # -----------------------------------------------------------------------

    def __add_summary(self, parent: HTMLNode):
        value = f"""
                <span>{get_msg(MSG_VISIBILITY)}</span>
                <button class="accordion-action" data-toggle
                        onclick="docManager.getToggleSelector().toggleSelection(event);"
                        onkeydown="docManager.getToggleSelector().toggleSelection(event);">
                    <img src="" alt="" />
                </button>
        """
        summary = HTMLNode(parent.identifier, None, "summary", value=value)
        summary.add_attribute("class", "summary-choice")
        parent.append_child(summary)

    # -----------------------------------------------------------------------

    def __add_main(self, parent: HTMLNode):
        main = HTMLNode(parent.identifier, None, "main")
        parent.append_child(main)
        ul = HTMLNode(main.identifier, None, "ul")
        main.append_child(ul)
        for field in DOC_FIELDS:
            field_property = DOC_FIELDS[field]

            # Add only toggable columns of the table
            if field_property.is_toggable is False:
                continue
            li = HTMLNode(ul.identifier, None, "li", attributes={"class": "check-item"})
            ul.append_child(li)

            # input
            inp = HTMLNode(li.identifier, field+"_input", "input")
            li.append_child(inp)
            inp.add_attribute("id", field+"_input")
            inp.add_attribute("type", "checkbox")
            inp.add_attribute("aria-labelledby", field+"_label")
            inp.add_attribute("data-toggle", field)
            if field_property.is_hidden is False:
                inp.add_attribute("checked", "checked")

            # label
            label = HTMLNode(li.identifier, field+"_label", "label", value=field_property.label)
            li.append_child(label)
            label.add_attribute("id", field+"_label")
            label.add_attribute("for", field+"_input")

# ---------------------------------------------------------------------------


class DocumentsNode(HTMLNode):
    """A node to show the list of documents in a table.

    Requires a global JS "docManager" which is an instance of "DocumentsManager()".
    Requires a global JS "asideManager which is an instance of "AsideManager()".

    """

    def __init__(self, parent: str, doc_manager: WhakerKitDocsManager = None, current_user: str = ""):
        """Create the node instance.

        :param parent: (str) The parent node identifier
        :param doc_manager: (WhakerKitDocsManager) Contains the list of documents to display in the table
        :param current_user: (str) The identified user -- can perform actions on files

        """
        super(DocumentsNode, self).__init__(parent, "documents_table", "table",
                                            attributes={"id": "documents_table", "role": "grid"})
        if doc_manager is None:
            self.__doc_manager = WhakerKitDocsManager()
            self.__doc_manager.collect_docs()

        elif isinstance(doc_manager, WhakerKitDocsManager) is True:
            self.__doc_manager = doc_manager
        else:
            raise TypeError("Given doc_manager must be an instance of WhakerKitDocsManager. "
                            "Got {:s} instead".format(type(doc_manager)))

        self.__current_user = WhakerKitDocsManager.format_author(current_user)
        self.reset()

    # -----------------------------------------------------------------------

    def reset(self):
        """Reset the children to the default elements.

        Create the table content: a row is a document, a column is a property
        of the document.

        """
        # Delete the existing list of children
        self.clear_children()

        # Define header: describe columns
        thead = HTMLNode(self.identifier, "thead", "thead")
        self.append_child(thead)
        tr = HTMLNode(thead.identifier, None, "tr")
        thead.append_child(tr)
        for field in DOC_FIELDS:
            field_property = DOC_FIELDS[field]
            if field_property.is_sortable is True:
                th = DocumentsNode.__add_sortable_th(tr, field, field_property.label)
            else:
                th = DocumentsNode.__add_th(tr, field, field_property.label)
                if field_property.is_toggable is True:
                    th.add_attribute("data-sort", field)
            if field_property.is_hidden is True:
                th.add_attribute("class", "hidden")

        # At last, add actions column
        DocumentsNode.__add_th(tr, "actions", get_msg(MSG_ACTIONS))

        # Append all rows
        tbody = HTMLNode(self.identifier, "tbody", "tbody")
        self.append_child(tbody)
        if len(self.__doc_manager) > 0:
            self.__fill_in_table(tbody)

    # -----------------------------------------------------------------------

    @staticmethod
    def __add_sortable_th(parent: HTMLNode, column_name, value=""):
        """Add a th to the parent node.

        column_name is used for both the sorting and the styling of the 'th'.

        """
        th = HTMLNode(parent.identifier, None, "th", attributes={"id": column_name+"_th"})
        b = HTMLNode(th.identifier, None, "button", value=value,
                     attributes={"class": "sortatable", "data-sort": column_name})
        th.append_child(b)
        parent.append_child(th)
        return th

    @staticmethod
    def __add_th(parent: HTMLNode, column_name, value=""):
        """Add a th to the parent node.

        column_name is used for the styling of the 'th'.

        """
        th = HTMLNode(parent.identifier, None, "th", attributes={"id": column_name+"_th"},
                      value=value)
        parent.append_child(th)
        return th

    # -----------------------------------------------------------------------

    def __fill_in_table(self, tbody: HTMLNode):
        """Add documents to the table."""
        for doc in self.__doc_manager.get_docs_sorted_by_most_viewed():

            tr = HTMLNode(tbody.identifier, None, "tr")
            tr.add_attribute("id", doc.folder_name)
            tbody.append_child(tr)

            for field in DOC_FIELDS:
                field_property = DOC_FIELDS[field]
                td = HTMLNode(tr.identifier, None, "td")
                tr.append_child(td)
                if field_property.is_hidden is True:
                    td.add_attribute("class", "hidden")

                if field == "filename":
                    td.set_value(doc.filename)
                elif field == "author":
                    td.set_value(doc.author.replace(whakerkit.sg.FIELDS_NAME_SEPARATOR, " "))
                elif field == "filetype":
                    td.set_value(doc.filetype)
                elif field == "date":
                    td.set_value(doc.date.strftime("%Y-%m-%d"))
                elif field == "description":
                    td.set_value(doc.description)
                elif field == "downloads":
                    td.set_value(str(doc.downloads))

            # At last, add actions
            td = HTMLNode(tr.identifier, None, "td")
            tr.append_child(td)
            self.__add_actions_in_column(doc, td)

    # -----------------------------------------------------------------------

    def __add_actions_in_column(self, doc, td):
        # - show details
        self.__add_icon_button(td, f"asideManager.showDetails('{doc.folder_name}');",
                               whakerkit.sg.path + "statics/icons/info.png", get_msg(MSG_ACTION_DETAILS))
        # - download
        btn = WhakerKitDownloadNode(
            td.identifier, self.__doc_manager.get_doc_relative_path(doc),
            doc.folder_name, get_msg(MSG_DOWNLOAD))
        btn.add_attribute("class", "text-reveal-button")
        td.append_child(btn)
        # - delete & describe: restricted actions to authenticated users
        logging.debug(f"Document author: {doc.author}, current user: {self.__current_user}")
        if self.__current_user == doc.author:
            self.__add_icon_button(td, f"docManager.describeDocument('{doc.folder_name}');",
                                   whakerkit.sg.path + "statics/icons/describe.png", get_msg(MSG_ACTION_DESCRIBE))
            btn = self.__add_icon_button(td, f"docManager.deleteDocument('{doc.folder_name}')",
                                         whakerkit.sg.path + "statics/icons/delete.png", get_msg(MSG_ACTION_DELETE))
            btn.add_attribute("id", "delete_button")

    # -----------------------------------------------------------------------

    def __add_icon_button(self, parent, onclick, icon, label):
        btn = HTMLNode(parent.identifier, None, "button",
                       attributes={"onclick": onclick, "class": "text-reveal-button"})

        parent.append_child(btn)
        img = HTMLNode(btn.identifier, None, "img",
                       attributes={
                           "alt": "",
                           "src": icon,
                           "onclick": onclick})
        btn.append_child(img)
        span = HTMLNode(btn.identifier, None, "span", value=label, attributes={"onclick": onclick})
        btn.append_child(span)

        return btn
