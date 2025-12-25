"""
:filename: whakerkit.responses.docs_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system to display all available documents in a table.

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
from collections import Counter
from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg

from ..nodes import ToggleColumnsNode
from ..nodes import DocumentsNode
from ..nodes import WhakerKitDocAsideNode
from ..nodes import WhakerKitFilterNode
from ..uploads_manager import WhakerKitDocsManager
from ..config import TypesDealer
from ..documents import DocumentsFilters
from ..filters import FilteredSet

from .base import get_base_response_class  # WhakerKitResponse or Custom

# ---------------------------------------------------------------------------


MSG_TITLE_TAB = "Documents"
MSG_TITLE_DOCS = "Available documents"
MSG_UNRESPONDING = "The server did not respond to the request."
MSG_NB_DOCS = "There are {nb} documents"
MSG_NO_DOC = "No documents match the filters."
MSG_ALL_DOCS = "All documents match the filters."
MSG_NO_FILETYPE = "At least one file type must be checked."
MSG_NO_AUTHOR = "At least one author must be checked."
MSG_NO_FILTER = "No filter has been applied."
MSG_ARE_FILTERED = " that match the filters"

# ---------------------------------------------------------------------------
# Javascript to manage documents.
# ---------------------------------------------------------------------------


BODY_SCRIPT = """
    import {{ AsideManager }} from './whakerkit/statics/js/doc_details.js';
    import {{ DocumentsManager }} from './whakerkit/statics/js/documents.js';
    import {{ ToggleSelector }} from '../../../whakerexa/wexa_statics/js/wexa.js';
    
    // Create the manager for the details of a document
    let asideManager = new AsideManager();
    asideManager.handleAsideManagerOnLoad();
    window.asideManager = asideManager;

    // Create an instance of a document manager. 
    // Documents are displayed in a table with sortable rows.
    let docManager = new DocumentsManager("documents_table", "toggable_details");
    // Turn manager messages into custom language
    docManager.errorMessage = "{:s}";
    // Clear existing filters
    docManager.clearEntriesInContainer("filters_details");

    // Attach both to the window to be global -- allows "onclick" in buttons
    window.docManager = docManager;
    
    // Create the toggle selectors for the author/filetype filters
    let toggleSelectorAuthor = new ToggleSelector("{:s}", "author_details");
    let toggleSelectorFiletype = new ToggleSelector("{:s}", "filetype_details");
    window.toggleSelectorAuthor = toggleSelectorAuthor;
    window.toggleSelectorFiletype = toggleSelectorFiletype;    
    
""".format(get_msg(MSG_UNRESPONDING), whakerkit.sg.whakerexa+"icons", whakerkit.sg.whakerexa+"/icons")

# ---------------------------------------------------------------------------


class DocsResponse(get_base_response_class()):
    """The bake system for the page with all stored documents.

    """

    def __init__(self):
        super(DocsResponse, self).__init__(name=None, title=get_msg(MSG_TITLE_TAB))
        # Collect all stored documents.
        self.__doc_manager = WhakerKitDocsManager()
        self.__doc_manager.collect_docs()

    # -----------------------------------------------------------------------

    def create(self) -> None:
        """Override. Create the page tree.

        Set page name and add required js in the tree->head.

        """
        get_base_response_class().create(self)
        self.set_pagename("documents.html")

        js = "module"
        css = "text/css"

        # CSS/JS to have documents in a sortable table, with toggles to show/hide columns
        self._htree.head.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/sortatable.css", link_type=css)
        self._htree.head.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/toggleselect.css", link_type=css)

        # JS to show/hide detailed information on a document
        self._htree.head.script(src=whakerkit.sg.path + "statics/js/doc_details.js", script_type=js)

        # Create an instance of DocumentsManager() and load the JS to perform
        # actions on documents - e.g. filter.
        self._htree.head.script(src=whakerkit.sg.path + "statics/js/documents.js", script_type=js)

        # Create docManager instance after the page is loaded.
        new_body_script = HTMLNode(self._htree.get_body_identifier(), "body_script",
                                   "script", value=BODY_SCRIPT)
        new_body_script.add_attribute("type", js)
        self._htree.set_body_script(new_body_script)

    # -----------------------------------------------------------------------

    def set_pagename(self, page_name: str):
        """Set the name of this page as seen in the url.

        :param page_name: (str) Name of the HTML page.

        """
        self._page_name = page_name

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events: (dict) the posted events
        :param kwargs: (dict) the keyword arguments
        :return: (bool) True to bake the page, False otherwise

        """
        logging.debug(f"DocumentsResponse._process_events: {events.keys()}.")

        # Default HTTP status: OK
        self._status.code = 200

        # Received events
        if "event_name" in events:
            if events["event_name"] == "increment_downloads":
                # The document identified by 'folder_name' was downloaded.
                folder_name = events.get('folder_name', '')
                if len(folder_name) > 0:
                    nb = self.__doc_manager.increment(folder_name)
                    self._data["downloads"] = nb
                    return False

            elif events["event_name"] == "filter_documents":
                filters = events.get('filters', {})
                if len(filters) > 0:
                    conditions = events.get("conditions", {})
                    content = self.get_filtered_documents(filters, conditions)
                    if len(content) > 0:
                        self._status.code = 200
                        self._data["content"] = content
                    else:
                        self._status.code = 400
                    return False
                else:
                    # Log and send the problem.
                    logging.error("Requested to filter documents with no given filters!")
                    self._status.code = 400
                    self._data["error"] = "Requested to filter documents with no given filters!"

        # Must bake the page
        return True

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Create the dynamic content in the body->main of the page.

        """
        h1 = self._htree.element("h1")
        h1.set_value(get_msg(MSG_TITLE_DOCS))
        self.__append_filters()
        self.__append_hidden_dialogs()
        div = self._htree.element("div")
        div.set_attribute("id", "documents_div")
        self.__append_documents(div, self.__doc_manager)

    # -----------------------------------------------------------------------

    def __append_hidden_dialogs(self):
        """Append the hidden dialogs for info and error.

        """
        # A hidden dialog to display an error message after a posted event
        dlg = self._htree.element("dialog")
        dlg.add_attribute("id", "error_dialog")
        dlg.add_attribute("role", "alertdialog")
        dlg.add_attribute("class", "error hidden-alert")

        # A hidden dialog to display an info message after a posted event
        dlg = self._htree.element("dialog")
        dlg.add_attribute("id", "info_dialog")
        dlg.add_attribute("role", "alertdialog")
        dlg.add_attribute("class", "info hidden-alert")

    # -----------------------------------------------------------------------

    def __append_filters(self):
        """Append a section with filters for documents.

        """
        docs_filter = WhakerKitFilterNode(self._htree.body_main.identifier,
                                          self.get_all_filetypes(),
                                          self.get_all_authors())
        self._htree.body_main.append_child(docs_filter)

    # -----------------------------------------------------------------------

    @staticmethod
    def __append_documents(parent: HTMLNode, doc_manager: WhakerKitDocsManager, filtered=False):
        """Append a section with the documents.

        """
        p_value = get_msg(MSG_NB_DOCS.format(nb=len(doc_manager)))
        if filtered is True:
            p_value += get_msg(MSG_ARE_FILTERED)

        p = HTMLNode(parent.identifier, None, "p", value=p_value+".")
        parent.append_child(p)

        # Add a node with a table displaying the list of requested documents:
        # all of them or only the filtered ones, with a toggle selector.
        selector = ToggleColumnsNode(parent.identifier)
        parent.append_child(selector)
        all_docs = DocumentsNode(parent.identifier, doc_manager)
        parent.append_child(all_docs)

        # Add a node to display the details of a specified document
        aside = WhakerKitDocAsideNode(parent.identifier)
        parent.append_child(aside)

    # -----------------------------------------------------------------------
    # Methods
    # -----------------------------------------------------------------------

    def get_all_filetypes(self):
        """Get all file types.

        :return: (list) File types

        """
        filetypes = [doc.filetype for doc in self.__doc_manager]
        return list(set(filetypes))

    # -----------------------------------------------------------------------

    def get_all_authors(self):
        """Get all authors.

        :return: (list) Authors

        """
        # Get the author of each document and sort alphabetically
        authors = sorted([doc.author for doc in self.__doc_manager])
        # Count the number of each element
        counts = Counter(authors)
        # Return author by most frequent
        return [item for item, count in counts.most_common()]

    # -----------------------------------------------------------------------

    def get_filtered_documents(self, filters: dict, conditions: dict) -> str:
        """Return the serialized content with the list of filtered documents.

        :param filters: (dict) the filters
        :param conditions: (dict) the conditions
        :return: (str)

        """
        logging.debug(" ... Get all the filtered documents into an HTML table")
        filters_match_all = conditions.get('general_condition', True)
        descr_cond = conditions.get('description_condition', "acontains")
        descr_match_all = conditions.get('switch_description', True)

        logging.debug(f" ... ... Filters: {filters}")
        logging.debug(f" ... ... Match all filters (and): {filters_match_all} -> {type(filters_match_all)}")
        logging.debug(f" ... ... Descr condition: {descr_cond}")
        logging.debug(f" ... ... Description match all (and): {descr_match_all} -> {type(descr_match_all)}")
        try:
            docs = self.__filter_documents(filters, descr_cond, filters_match_all, descr_match_all)
            manager = WhakerKitDocsManager()
            manager.add_docs(docs)
            div = HTMLNode(None, None, "div")
            self.__append_documents(div, manager, filtered=True)
        except Exception as e:
            logging.error(e)
            self._data = {"error": "Filter error. " + str(e)}
        else:
            return div.serialize()

        return ""

    # -----------------------------------------------------------------------

    def __filter_documents(self, filters: dict, descr_cond: str,
                           match_all: bool = True, match_all_descr: bool = True) -> list:
        """Apply given filters to the list of documents of the document manager.

        This method formats the given filters according to the expected
        format of the document manager and retrieves the filtered documents.

        :param filters: (dict) the filters
        :param match_all: (bool) the general condition to match all criteria (True by default)
        :param descr_cond: (str) the description condition ("acontains" by default)
        :param match_all_descr: (str) must match all tokens in description (True by default)
        :raises: ValueError:
        :raises: TypeError:
        :return: (list) List of filtered documents

        """
        # Check required filters: at least one author and one filetype
        filetypes = filters["filetype"]
        authors = filters["authors"]
        if self.__check_filters(filetypes, authors) is False:
            return list()

        filtered_sets = list()

        # Filter documents based on filetype. Do not filter if all filetypes are given.
        if self.are_equals(filetypes, self.get_all_filetypes()) is False:
            filtered_sets.append(self.__filter_by_filetype(filetypes))

        # Filter documents based on authors. Do not filter if all authors are given.
        if self.are_equals(authors, self.get_all_authors()) is False:
            filtered_sets.append(self.__filter_by_authors(authors))

        # Filter documents based on date range. Do not filter if no date is given.
        if len(filters["dates"]["start"]) > 0 or len(filters["dates"]["end"]) > 0:
            filtered_sets.append(self.__filter_by_dates(filters["dates"]))

        # Filter documents based on description. Do not filter if no description.
        if len(filters["description"].strip()) > 0:
            filtered_sets.append(self.__filter_by_description(filters["description"], descr_cond, match_all_descr))

        # No filter was defined. Return all documents.
        if len(filtered_sets) == 0:
            self._data = {'info': get_msg(MSG_NO_FILTER)}
            return [d for d in self.__doc_manager]

        # Return the filtered documents.
        filtered_docs = self.__merge_and_log(filtered_sets, match_all)
        return [doc for doc in filtered_docs]

    # -----------------------------------------------------------------------

    def __merge_and_log(self, filtered_sets: list, match_all: bool) -> FilteredSet:
        if match_all is False:
            # OR condition between all filters. Append all documents to match with.
            f = FilteredSet()
            for doc in self.__doc_manager:
                f.append(doc)
            filtered_sets.append(f)

        # Apply merging
        logging.info(f"Merging filtered sets: {filtered_sets} ({len(filtered_sets)} filters), with match-all: {match_all}.")
        filtered_docs = DocumentsFilters.merge_data(filtered_sets, match_all)

        logging.info(f"Found {len(filtered_docs)} documents.")
        if len(filtered_docs) == 0 or len(filtered_docs) == len(self.__doc_manager):
            if len(filtered_docs) == 0:
                self._data = {'info': get_msg(MSG_NO_DOC)}
                logging.info("None of the documents is matching the filters.")
            else:
                self._data = {'info': get_msg(MSG_ALL_DOCS)}
                logging.info("All documents are matching the filters.")
        else:
            logging.info(f"{len(self.__doc_manager)} documents are matching the filters.")

        return filtered_docs

    # -----------------------------------------------------------------------

    def __check_filters(self, filetypes: list, authors: list) -> bool:
        if len(filetypes) == 0:
            self._data = {"info": get_msg(MSG_NO_FILETYPE)}
            return False
        if len(authors) == 0:
            self._data = {"info": get_msg(MSG_NO_AUTHOR)}
            return False
        return True

    # -----------------------------------------------------------------------

    def __filter_by_filetype(self, selected_filetypes: list) -> FilteredSet:
        """Filter documents by filetype.

        :param selected_filetypes: (list) the selected filetypes to filter by
        :return: (FilteredSet) Set of documents

        """
        formatted_filters = [("filetype", "iexact", selected_filetypes)]
        logging.info(f"Applying filetype filters: {formatted_filters}.")
        return self.__apply_filters(formatted_filters, False)

    # -----------------------------------------------------------------------

    def __filter_by_authors(self, selected_authors: list):
        """Filter documents by authors.

        :param selected_authors: (list) the selected authors to filter by
        :return: (FilteredSet) Set of documents

        """
        formatted_filters = [("author", "iexact", selected_authors)]
        return self.__apply_filters(formatted_filters, False)

    # -----------------------------------------------------------------------

    def __filter_by_dates(self, date_filters: dict):
        """Filter documents by date range.

        :param date_filters: (dict) dictionary containing start and end dates
        :return: (FilteredSet) Set of documents

        """
        formatted_filters = list()
        if date_filters["start"]:
            formatted_filters.append(("date", "ge", [f"{date_filters['start']}-01-01"]))
        if date_filters["end"]:
            formatted_filters.append(("date", "le", [f"{date_filters['end']}-12-31"]))

        if len(formatted_filters) > 0:
            return self.__apply_filters(formatted_filters, True)
        return FilteredSet()

    # -----------------------------------------------------------------------

    def __filter_by_description(self, description: str, descr_cond: str, match_all_descr: bool) -> FilteredSet:
        """Filter documents by description.

        :param description: (str) the description filter
        :param descr_cond: (str) the condition for filtering description
        :param match_all_descr: (bool) True if all tokens of the description should be matched
        :return: Filtered set of documents or None if no filter applied

        """
        if descr_cond not in ("contains", "not_contains"):
            description = TypesDealer.remove_diacritics_and_non_ascii(description)
        tokens = description.split(" ")

        if match_all_descr is True:
            filtered_set = None
            for token in tokens:
                formatted_filters = list()
                formatted_filters.append(("filename", descr_cond, [token]))
                formatted_filters.append(("description", descr_cond, [token]))
                f = self.__apply_filters(formatted_filters, "not" in descr_cond)
                if filtered_set is None:
                    filtered_set = f
                else:
                    filtered_set = f & filtered_set
                    if len(filtered_set) == 0:
                        return filtered_set
            return filtered_set
        else:
            formatted_filters = list()
            formatted_filters.append(("filename", descr_cond, tokens))
            formatted_filters.append(("description", descr_cond, tokens))

        return self.__apply_filters(formatted_filters, "not" in descr_cond)

    # -----------------------------------------------------------------------

    def __apply_filters(self, formatted_filters, match_all):
        logging.info(f"Apply filters: {formatted_filters}.")
        return self.__doc_manager.filter_docs(formatted_filters, match_all, out_filterset=True)

    # -----------------------------------------------------------------------

    @staticmethod
    def are_equals(l1: list, l2: list) -> bool:
        """Check if two lists contain the same elements, regardless of order.

        :param l1: (list) First list of elements.
        :param l2: (list) Second list of elements.
        :return: (bool) True if both lists contain the same elements, False otherwise.

        """
        # Convert both lists to sets and compare them
        return set(l1) == set(l2)
