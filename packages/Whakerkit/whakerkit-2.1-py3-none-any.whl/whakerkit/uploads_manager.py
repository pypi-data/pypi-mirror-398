# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.uploads_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Manage the locally stored documents.

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

import whakerkit
from .config import TypesDealer
from .documents import DocumentsManager
from .documents import Document
from .documents import ImmutableDocument

import whakerkit

# ---------------------------------------------------------------------------


class WhakerKitDocsManager(DocumentsManager):

    def __init__(self):
        super(WhakerKitDocsManager, self).__init__(
            whakerkit.sg.uploads, absolute_path=whakerkit.sg.root_path)

    # -----------------------------------------------------------------------

    @staticmethod
    def format_filename(filename: str) -> str:
        """Return the formatted filename for the documents.

        Format a given filename by removing diacritics and non-ASCII characters,
        ensuring compatibility for a web usage. Trims the filename to a maximum
        length of 64 characters.

        :param filename: (str) The filename to format.
        :return: (str) The formatted filename, limited to 64 characters.

        """
        TypesDealer.check_types("WhakerKitDocsManager.format_filename", [(filename, str)])
        filename = TypesDealer.remove_diacritics_and_non_ascii(filename)
        return filename[:64]

    # -----------------------------------------------------------------------

    @staticmethod
    def format_author(author: str) -> str:
        """Return the formatted author name for the documents.

        Format a given author's name by removing diacritics and non-ASCII characters,
        ensuring compatibility for a web usage.

        :param author: (str) The author's full name to format.
        :return: (str) The formatted author name.

        """
        TypesDealer.check_types("WhakerKitDocsManager.format_author", [(author, str)])
        author = TypesDealer.remove_diacritics_and_non_ascii(author)
        return author.replace(" ", whakerkit.sg.FIELDS_NAME_SEPARATOR)

    # -----------------------------------------------------------------------

    @staticmethod
    def format_description(description: str) -> str:
        """Return the formatted description for the documents.

        Format a given description by removing multiple spaces, CR/LF and TAB
        characters.

        :param description: (str) The description to format.
        :return: (str) The formatted description, limited to 160 characters.

        """
        TypesDealer.check_types("WhakerKitDocsManager.format_description", [(description, str)])
        description = TypesDealer.strip_string(description)
        return description[:160]

    # -----------------------------------------------------------------------

    @staticmethod
    def data_attributes(doc: Document | ImmutableDocument) -> dict:
        """Create a dictionary with the data of the given doc.

        :param doc: (Document | ImmutableDocument) The document to get information from
        :return: (dict) details of the document

        """
        attributes = dict()
        attributes["data-name"] = doc.filename
        attributes["data-author"] = doc.author
        attributes["data-type"] = doc.filetype
        attributes["data-date"] = doc.date.strftime("%Y-%m-%d")
        attributes["data-description"] = doc.description
        attributes["data-downloads"] = str(doc.downloads)
        return attributes

    # -----------------------------------------------------------------------

    def increment(self, folder_name: str) -> int:
        """Increment the number of downloads of a document.

        The given filepath starts with the full path of the "uploads" folder
        on the server. Then it has the folder name of the document followed
        by the filename with its extension, for example:
        /somewhere/web/uploads/Author_2024-06-17_html_bienvenue/bienvenue.html

        :param folder_name: (str) Identifier of a document.
        :raises: ValueError: if the filepath does not start with the full path of the "uploads" folder
        :return: (int) new number of downloads

        """
        # Create a document object
        document = Document.create_document_by_folder_name(folder_name)
        # Increment this document nb of downloads
        nb = self.increment_doc_downloads(document)
        # Add logging for tracking increment operations
        logging.debug(f"Incremented downloads for document {folder_name} to {nb}")
        return nb
