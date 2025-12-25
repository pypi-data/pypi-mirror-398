# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.responses.deposit_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system for the deposit page.

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

from ..nodes.docs_node import DocumentsNode
from ..nodes.doc_aside_node import WhakerKitDocAsideNode
from ..nodes.utils import create_action_button
from ..nodes.login_node import WhakerKitLoginNode
from ..uploads_manager import WhakerKitDocsManager
from ..documents import Document
from ..documents import ImmutableDocument

from .base_auth_resp import WhakerkitAuthResponse

# ---------------------------------------------------------------------------


MSG_TITLE_TAB = "Deposits"
MSG_TITLE_DEPOSIT = "My deposits"
MSG_NOT_AUTH = "The content of this page is access-restricted [...]"
MSG_LOGIN = "Log in"
MSG_LOGOUT = "Log out"
MSG_CONNECTED = "You are logged in."

MSG_UPLOAD_DOC = "Upload a document"
MSG_MANAGE_DOC = "Manage uploaded documents of {author}"
MSG_NO_DOCS = "You have not deposited any documents."
MSG_NB_DOCS = "You have deposited {nb_docs} documents."
MSG_SEND_FILE = "Send"
MSG_PLEASE_WAIT = "Uploading... Please wait."
MSG_VALIDATE = "Validate"
MSG_FILENAME_INFO = "The uploaded document will be visible to all users [...]"
MSG_FILENAME_RECOMMANDATION = "Consider depositing your file with a name that [...]"

MSG_UPLOAD_FAILED = "Error saving the document on the server"
MSG_NO_DESCRIPTION = "No description provided."
MSG_NEW_DESCR = "New description for the referenced document:"
MSG_MAX_LEN_DESCR = "/ 160 characters"
MSG_UNRESPONDING = "The server did not respond to the request."
MSG_EMPTY_FILE = "The file upload was not completed: the file is empty."
MSG_NON_AUTHORIZED = "You are not authorized to make changes to this document."
MSG_SERVER_ERROR = "The following error occurred: {error}"

# ---------------------------------------------------------------------------
# Javascript to manage documents.
# ---------------------------------------------------------------------------


BODY_SCRIPT = f"""
    import {{ AsideManager }} from '/{whakerkit.sg.path}statics/js/doc_details.js';
    import {{ DocumentsManager }} from '/{whakerkit.sg.path}statics/js/documents.js';

    // Create the manager for the details of a document
    let asideManager = new AsideManager();
    asideManager.handleAsideManagerOnLoad();
    window.asideManager = asideManager;

    // Create an instance of a document manager.
    // Documents are displayed in a table with sortable rows but without toggle_details.
    let docManager = new DocumentsManager("documents_table");
    // Turn manager messages into custom language
    docManager.errorMessage = "{get_msg(MSG_UNRESPONDING)}";

    // Attach both to the window to be global -- allows "onclick" in buttons
    window.docManager = docManager;

"""


# ---------------------------------------------------------------------------


class DepositResponse(WhakerkitAuthResponse):
    """The bake system for the page with documents of an authenticated user.

    Declare a global JS "docManager" which is an instance of "DocumentsManager()".
    Declare a global JS "asideManager which is an instance of "AsideManager()".

    """

    def __init__(self, name: str = None):
        super(DepositResponse, self).__init__(name, title=get_msg(MSG_TITLE_TAB))
        self.__doc_manager = WhakerKitDocsManager()

    # -----------------------------------------------------------------------

    def create(self):
        """Create the deposit page.

        """
        WhakerkitAuthResponse.create(self)
        self.set_pagename("depot_perso.html")

        # CSS/JS to have documents in a sortable table
        self._htree.head.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/sortatable.css", link_type="text/css")

        # JS to perform an action on a document with an instance of DocumentsManager():
        # upload/delete/set description
        self._htree.head.script(src=whakerkit.sg.path + "statics/js/documents.js", script_type="module")

        # JS to show/hide detailed information on a document
        self._htree.head.script(src=whakerkit.sg.path + "statics/js/doc_details.js", script_type="module")

        # Create docManager instance after the page is loaded.
        new_body_script = HTMLNode(self._htree.get_body_identifier(), "body_script",
                                   "script", value=BODY_SCRIPT)
        new_body_script.add_attribute("type", "module")
        self._htree.set_body_script(new_body_script)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events: (dict) the posted events
        :param kwargs: (dict) the keyword arguments
        :return: (bool) True to bake the page, False otherwise

        """
        # Default HTTP status: OK
        self._status.code = 200

        # Call the parent method to manage login events
        has_auth = WhakerkitAuthResponse._process_events(self, events, **kwargs)
        if has_auth is True:
            # Authenticated with login/password
            if self._status.code == 200:
                self.bake(self._data)
            return True

        logging.debug(f"DepositResponse._process_events: {events.keys()}.")

        # Authentication with a token
        token = events.get('token')
        if token is not None:
            WhakerkitAuthResponse.authenticate(self, events.get("token", ""))

        # Catch events requiring an authenticated user.
        if self._is_authenticated is True:
            self._data["token"] = token

            logging.info(f" ... Authenticated user: {self._author}")
            self.__doc_manager.collect_docs()

            # Upload event
            if "upload_file" in events:
                return self.__upload_callback(events["upload_file"])

            elif events.get("event_name", "") == "delete_document":
                return self.__delete_callback(events)

            elif events.get("event_name", "") == "describe_document":
                return self.__describe_callback(events)

            elif events.get("event_name", "") == "increment_downloads":
                # The author downloaded one of his/her document. Do nothing!
                return False

            else:
                self.__no_event_callback()

        return True

    # -----------------------------------------------------------------------
    # Callback to events
    # -----------------------------------------------------------------------

    def __no_event_callback(self) -> bool:
        """Manage the callback when no event.

        :return: (bool) True to bake the page, False otherwise

        """
        try:
            self._data["content"] = self.get_documents()
            self._status.code = 200
            return True
        except Exception as e:
            logging.error(f"Error while retrieving documents: {e}")
            self._data = {"error": str(e)}
            self._status.code = 400
            return False

    # -----------------------------------------------------------------------

    def __upload_callback(self, upload_event: dict) -> bool:
        """Manage the callback for the upload_file event.

        The given event is a dictionary like for example:
        {'filename': 'robots.txt', 'mime_type': 'text/plain', 'file_content': 'User-agent: *\n'}}

        :param upload_event: (dict) the upload event
        :return: (bool) True to bake the page, False otherwise

        """
        content = upload_event.get("file_content", "")
        filename = upload_event.get("filename", "")
        logging.debug(" -- DepositResponse.__upload_callback filename: %s", filename)
        logging.debug(" -- DepositResponse.__upload_callback content length: %s", len(content))

        if len(content) == 0:
            # The request was well-formed but could not be processed.
            self._status.code = 422
            self._data = {"error": get_msg(MSG_EMPTY_FILE)}
            logging.error(f"File {filename} is empty.")
        else:
            try:
                self.upload_document(filename, content)
                logging.info(f"File {filename} saved successfully.")
                self._status.code = 200
                return True
            except Exception as e:
                self._status.code = 400
                logging.error(f"Error while saving file {filename}: {e}")
                self._data = {"error": get_msg(MSG_UPLOAD_FAILED) + " " + str(e)}

        return False

    # -----------------------------------------------------------------------

    def __describe_callback(self, describe_event: dict) -> bool:
        """Manage the callback for the describe_document event.

        :param describe_event: (dict) the descript event
        :return: (bool) True to bake the page, False otherwise

        """
        folder_name = describe_event.get("folder_name", "")
        description = describe_event.get("description", "")
        self._status.code = 401

        description = WhakerKitDocsManager.format_description(description)
        if len(description) == 0:
            self._data = {"error": get_msg(MSG_NO_DESCRIPTION)}
        else:
            try:
                # Save the description
                self.describe_document(folder_name, description)
                self._status.code = 200
                return True
            except Exception as e:
                logging.error(f"Error while saving description: {e}")
                self._data = {"error": get_msg(MSG_SERVER_ERROR) + " " + str(e)}

        return False

    # -----------------------------------------------------------------------

    def __delete_callback(self, delete_event: dict) -> bool:
        """Manage the callback for the delete_document event.

        :param delete_event: (dict) the descript event
        :return: (bool) True to bake the page, False otherwise

        """
        folder_name = delete_event.get("folder_name", "")
        self._status.code = 401

        try:
            # Save the description
            self.delete_document(folder_name)
            self._status.code = 200
            return True
        except Exception as e:
            logging.error(f"Error while saving description: {e}")
            self._data = {"error": get_msg(MSG_SERVER_ERROR) + " " + str(e)}

        return False

    # -----------------------------------------------------------------------
    # Bake the page
    # -----------------------------------------------------------------------

    def _bake(self):
        """Create the dynamic page content in HTML.

        """
        if self._is_authenticated is True:
            # Force a refresh in 31 minutes!
            self._htree.head.meta({"http-equiv": "refresh", "content": "1860"})

        self.__append_title()
        self.__bake_anonymous()
        self.__bake_authenticated()

    # -----------------------------------------------------------------------

    def __bake_anonymous(self):
        """Add dynamic body->main content for an un-authenticated user.

        """
        section = self._htree.element("section")
        section.add_attribute("id", "anonymous_section")

        me = HTMLNode(section.identifier, None, "p", value=get_msg(MSG_NOT_AUTH))
        section.append_child(me)

        # Create the login dialog
        login_node = WhakerKitLoginNode(section.identifier)
        section.append_child(login_node)

        # Add a button to open the modal dialog
        if logging.getLogger().getEffectiveLevel() > 1:
            action = "window.Wexa.dialog.open('" + login_node.identifier + "', true)"
        else:
            action = "authManager.submitLogin('anonymous', '********');"
        btn = create_action_button(section.identifier, action, get_msg(MSG_LOGIN), whakerkit.sg.path + "statics/icons/authentication.png")
        section.append_child(btn)

    # -----------------------------------------------------------------------

    def __bake_authenticated(self):
        """Add dynamic body->main for an authenticated user.

        """
        section = self._htree.element("section")
        section.add_attribute("id", "authenticated_section")

        # Message to display the author is connected
        me = HTMLNode(section.identifier, None, "p", value=get_msg(MSG_CONNECTED))
        section.append_child(me)

        # Add a button to log out the user -- it will delete its token.
        token = self._data.get("token", "")
        if token is not None:
            action = "authManager.submitLogout('" + self._data.get("token", "") + "');"
        else:
            action = ""
        btn = create_action_button(section.identifier, action, get_msg(MSG_LOGOUT), whakerkit.sg.path + "statics/icons/log-out.png")
        btn.add_attribute("type", "submit")
        if token is None:
            btn.add_attribute("disabled", None)
        section.append_child(btn)

        stitle = HTMLNode(section.identifier, None, "h2", value=get_msg(MSG_UPLOAD_DOC))
        section.append_child(stitle)

        ssection = HTMLNode(section.identifier, None, "section")
        ssection.add_attribute("class", "flex-panel")
        section.append_child(ssection)

        left = HTMLNode(ssection.identifier, None, "article")
        left.add_attribute("class", "flex-item width_60")
        ssection.append_child(left)
        self.__append_file_sending(left)

        right = HTMLNode(ssection.identifier, None, "dialog", value=get_msg(MSG_FILENAME_RECOMMANDATION))
        right.add_attribute("class", "flex-item width_40 tips")
        right.add_attribute("role", "alertdialog")
        ssection.append_child(right)

        # The list of documents of the authenticated user
        subsection = HTMLNode(section.identifier, None, "section")
        subsection.set_attribute("id", "authenticated_content")
        section.append_child(subsection)

    # -----------------------------------------------------------------------

    def __append_title(self):
        """Append the title."""
        h1 = self._htree.element("h1")
        h1.set_value(get_msg(MSG_TITLE_DEPOSIT))

        # A dialog to display any error message after a posted event
        dlg = self._htree.element("dialog")
        dlg.add_attribute("id", "error_dialog")
        dlg.add_attribute("role", "alertdialog")
        dlg.add_attribute("class", "error hidden-alert")

        # A dialog to display any information message after a posted event
        dlg = self._htree.element("dialog")
        dlg.add_attribute("id", "wait_dialog")
        dlg.add_attribute("role", "alertdialog")
        dlg.add_attribute("class", "info hidden-alert")
        dlg.set_value(get_msg(MSG_PLEASE_WAIT))

    # -----------------------------------------------------------------------

    def __append_file_sending(self, parent: HTMLNode):
        """Append a section to send a new document.

        """
        fn_info = HTMLNode(parent.identifier, None, "p", value="<br>"+get_msg(MSG_FILENAME_INFO))
        parent.append_child(fn_info)

        input_file = HTMLNode(parent.identifier, None, "input",
                              attributes={'id': "file_input", 'type': "file", 'name': 'file_input'})
        parent.append_child(input_file)

        # The action button
        btn = create_action_button(parent.identifier, "docManager.sendDocument();",
                                   get_msg(MSG_SEND_FILE), whakerkit.sg.path + "statics/icons/upload.png")
        btn.add_attribute("type", "submit")
        parent.append_child(btn)

    # -----------------------------------------------------------------------

    def __append_all_docs(self, parent: HTMLNode, documents: list):
        """Append the table with all documents to the body->main.

        It's a table element with all documents of the authenticated author.

        """
        stitle = HTMLNode(parent.identifier, None, "h2",
                          value=get_msg(MSG_MANAGE_DOC).format(author=self._author))
        parent.append_child(stitle)

        if documents is not None:
            # Create a document manager
            dm = WhakerKitDocsManager()
            if len(documents) == 0:
                no = HTMLNode(parent.identifier, None, "p", value=get_msg(MSG_NO_DOCS))
                parent.append_child(no)
                # Display no document in a table
                file_node = DocumentsNode(parent.identifier, dm, self._author)
            else:
                no = HTMLNode(parent.identifier, None, "p",
                              value=get_msg(MSG_NB_DOCS).format(nb_docs=len(documents)))
                parent.append_child(no)
                # Create a dialog to set a new description
                descr_dlg = HTMLNode(parent.identifier, "description_dialog", "dialog",
                                     attributes={'id': "description_dialog"})
                descr_dlg.set_value(
                    f"""
                    <form method="dialog">
                        <p>{get_msg(MSG_NEW_DESCR)}<br><i><span id="folder_name_span"></span></i></p>
                        <textarea id="new_description_field" rows="3" cols="55" maxlength="160"
                                  onkeyup="docManager.currentDescriptionLength();"
                        ></textarea>
                        <p><small><span id="new_description_span">--</span>{get_msg(MSG_MAX_LEN_DESCR)}</small></p>
                        <menu>
                            <button id="confirm" type="submit">{get_msg(MSG_VALIDATE)}</button>
                        </menu>
                    </form>
                    """
                )
                parent.append_child(descr_dlg)
                # Create a panel to show the details -- hidden by default
                aside = WhakerKitDocAsideNode(parent.identifier)
                parent.append_child(aside)

                # Append the documents of the author
                dm.add_docs(documents)
                # Display these documents in a table
                file_node = DocumentsNode(parent.identifier, dm, self._author)
            # Add the table to the parent
            parent.append_child(file_node)

    # -----------------------------------------------------------------------
    # Functions available for an authenticated user only.
    # -----------------------------------------------------------------------

    def get_documents(self) -> str:
        """Return the serialized content with the list of author documents.

        :return: (str)

        """
        logging.info(" ... Get all the documents of the user from its author name")
        # Get all the documents of the user from its author name
        author = WhakerKitDocsManager.format_author(self._author)
        docs = self.__doc_manager.filter_docs([("author", "iexact", [author])])
        div = HTMLNode(None, None, "div")
        self.__append_all_docs(div, docs)
        return div.serialize()

    # -----------------------------------------------------------------------

    def describe_document(self, folder_name: str, description: str):
        """Describe a document in the list of existing ones.

        :param folder_name: (str) Name of the folder of a specific document
        :param description: (str) New description of the document

        """
        logging.info(f" ... Describe document in {folder_name} with description: {description}")
        # Create a Document() from the folder name
        doc = Document.create_document_by_folder_name(folder_name)

        # Check if the user is the author of the file
        if doc.author != WhakerKitDocsManager.format_author(self._author):
            raise Exception(get_msg(MSG_NON_AUTHORIZED))

        # Save the description
        self.__doc_manager.set_doc_description(doc, description)

    # -----------------------------------------------------------------------

    def delete_document(self, folder_name: str = ""):
        """Delete a document in the list of existing ones.

        :param folder_name: (str) Name of the folder of a specific document
        :return: (bool) True if the file was deleted successfully, False otherwise

        """
        logging.info(f" ... Delete document in {folder_name}")
        # Create a Document() from the folder name
        doc = Document.create_document_by_folder_name(folder_name)

        # Check if the user is the author of the file
        if doc.author != WhakerKitDocsManager.format_author(self._author):
            raise Exception(get_msg(MSG_NON_AUTHORIZED))

        # Delete the file
        self.__doc_manager.invalidate_doc(doc)

    # -----------------------------------------------------------------------

    def upload_document(self, filename: str, content: str | bytes) -> bool:
        """Save a given file as a document.

        :param filename: (str) Filename of the document to be uploaded
        :param content: (str) Document content
        :return: (bool) True if the document was uploaded, False otherwise

        """
        # Format the filename and author: for the web, diacritics are not allowed
        filename = WhakerKitDocsManager.format_filename(filename)
        author = WhakerKitDocsManager.format_author(self._author)

        logging.info(f"Upload document: {filename} from author: {author}")
        # Create a document object
        document = ImmutableDocument(
            author=author,
            filename=filename,
            content=content)

        # Save the document into a file
        self.__doc_manager.add_doc(document)
        return self.__doc_manager.save_doc(document)
