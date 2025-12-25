"""
:filename: whakerkit.documents.docs_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Management of a folder of documents.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io

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

    -------------------------------------------------------------------------

"""

from __future__ import annotations
import logging
import os
import shutil
import codecs

import whakerkit

from ..config.typesdealer import TypesDealer

from .document import Document
from .document import ImmutableDocument
from .docs_filters import DocumentsFilters

# ---------------------------------------------------------------------------


HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------


class DocumentsManager:
    """Management of a bunch of documents.

    """

    def __init__(self, folder_path: str = ".", absolute_path: str | None = None):
        """Initialize the DocumentsManager.

        The given folder is used to collect the documents from and write
        documents into. It must be a relative path, not an absolute one.
        The absolute path to this folder is indicated separately.

        It must exist.

        :example:
        >>> manager = DocumentsManager('test_folder')
        >>> manager.collect_docs()
        >>> print(manager.get_docs_sorted_by_newest())
        >>> # Assuming your_document is a document in the folder
        >>> manager.get_doc_content(your_document)
        >>> print(your_document.content)  # The content of the document is printed
        >>> manager.delete(your_document)
        >>> print(manager.get_docs_sorted_by_newest())  # The document is deleted

        :param folder_path: (str) The relative path of a folder
        :raises: TypeError: Invalid folder path type
        :raises: FileNotFoundError: The specified folder does not exist at the specified location

        """
        if absolute_path is None:
            logging.info(f"Absolute path not specified. Use default: {HERE}")
            absolute_path = HERE
        TypesDealer.check_types("DocumentsManager.__init__", [(folder_path, str), (absolute_path, str)])

        full_path = os.path.join(absolute_path, folder_path)
        if os.path.exists(full_path) is False:
            raise FileNotFoundError(f"The specified folder does not exist at the specified "
                                    f"location: '{full_path}'.")
        self.__folder_path = folder_path
        self.__absolute_path = absolute_path

        # List of collected Document() or ImmutableDocument() instances
        self.__docs = list()
        logging.debug(" ======================= INIT Documents Manager ===================== ")
        logging.debug(absolute_path)
        logging.debug(folder_path)
        logging.debug(full_path)

    # -----------------------------------------------------------------------
    # Getters and setters
    # -----------------------------------------------------------------------

    def get_folder_path(self) -> str:
        """Return the folder path: the relative path to documents.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> print(doc1.get_folder_path())  # test_folder

        :return: (str) The folder path

        """
        return self.__folder_path

    # -----------------------------------------------------------------------

    def get_absolute_folder_path(self) -> str:
        """Return the folder path: the abosolute path to documents.

        :return: (str) The path to documents

        """
        return os.path.join(self.__absolute_path, self.__folder_path)

    absolute_path = property(get_absolute_folder_path, None)

    # -----------------------------------------------------------------------
    # Management of the list of documents
    # -----------------------------------------------------------------------

    def collect_docs(self, mutable: bool = True) -> None:
        """Collect all documents from the folder path.

        :example:
        >>> manager = DocumentsManager('test_folder')
        >>> manager.collect_docs()
        >>> print([doc for doc in manager])

        :param mutable: (bool) False to store only ImmutableDocument() instances instead of Document() instance ones
        :raises: FileNotFoundError: The specified folder does not exist at the specified location

        """
        if os.path.isdir(self.absolute_path) is False:
            raise IOError(f'The specified folder does not exist: {self.absolute_path}')

        for folder_name in os.listdir(self.absolute_path):
            full_path = os.path.join(self.absolute_path, folder_name)
            if os.path.isdir(full_path) is True:
                try:
                    # Get the description from the file -- if existing
                    description = self.__read_info(folder_name, whakerkit.sg.DESCRIPTION_FILENAME)

                    # Get the number of downloads from the file -- if existing
                    d = self.__read_info(folder_name, whakerkit.sg.DOWNLOADS_FILENAME)
                    downloads = 0 if len(d) == 0 else int(d)

                    idoc = Document.create_document_by_folder_name(folder_name, description, downloads)
                    if idoc not in self.__docs:
                        if mutable is True:
                            self.__append(self.__immutable_to_document(idoc))
                        else:
                            self.__append(idoc)
                except Exception as e:
                    logging.error(f"Failed to collect a document for folder {folder_name}: {e}")

        if len(self.__docs) > 0:
            logging.info(f"Collected {len(self.__docs)} documents in {self.absolute_path}")
        else:
            logging.info(f"No documents found in {self.absolute_path}.")

    # -----------------------------------------------------------------------

    def clear_docs(self):
        """Clear the list of documents.

        :example:
        >>> manager = DocumentsManager('test_folder')
        >>> manager.collect_docs()
        >>> manager.clear_docs()
        >>> print([doc for doc in manager])
        []

        """
        self.__docs.clear()

    # -----------------------------------------------------------------------

    def __append(self, doc: Document | ImmutableDocument) -> bool:
        """Append a document into the collection.

        :param doc: (Document) The document to append.
        :return: (bool) True if the document was appended, False otherwise.

        """
        # Check if the document was not already collected
        if doc not in self.__docs:
            self.__docs.append(doc)
            return True
        return False

    # -----------------------------------------------------------------------

    def add(self, author: str, filename: str, **kwargs) -> ImmutableDocument:
        """Create and add a document to the list of documents.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # Assuming your_document is a document
        >>> doc1.add_doc(your_document)
        >>> print(doc1.is_in_docs(your_document))
        True

        :param author: (str) The document author
        :param filename: (str) The document filename
        :param kwargs: (dict) The keyword arguments to create the Document()
        :raises: TypeError: Cant create the document
        :raises: ValueError: Cant create the document
        :return: (ImmutableDocument) The created document

        """
        doc = Document(author, filename, **kwargs)
        self.__append(doc)
        return ImmutableDocument(author, filename, **kwargs)

    # -----------------------------------------------------------------------

    def add_doc(self, doc: Document | ImmutableDocument) -> None:
        """Add a document to the list of documents.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # Assuming your_document is a document
        >>> doc1.add_doc(your_document)
        >>> print(doc1.is_in_docs(your_document)) # True

        :param doc: (Document) The document to add
        :raises: TypeError: Invalid document type

        """
        TypesDealer.check_types("DocumentsManager.add_doc", [(doc, (Document, ImmutableDocument))])
        if isinstance(doc, ImmutableDocument) is True:
            doc = self.__immutable_to_document(doc)
        self.__append(doc)

    # -----------------------------------------------------------------------

    def add_docs(self, docs: list) -> None:
        """Add a list of documents into the actual list of documents.

        Do not add anything if any element in the list is incorrect.

        :example:
        >>> manager = DocumentsManager('test_folder')
        >>> manager.collect_docs()
        >>> # Assuming doc1 and doc2 are Document() instances
        >>> manager.add_docs([doc1, doc2])
        >>> manager.is_in_docs(doc1))
        True

        :param docs: (list) The list of documents to add
        :raises: TypeError: Invalid document type

        """
        TypesDealer.check_types("DocumentsManager.add_docs", [(docs, (list, tuple))])
        # Check all docs before adding -- allows to not add anything if at least one is invalid
        for doc in docs:
            TypesDealer.check_types("DocumentsManager.add_doc",
                                    [(doc, (Document, ImmutableDocument))])

        # Add each given document
        for doc in docs:
            if isinstance(doc, ImmutableDocument) is True:
                doc = self.__immutable_to_document(doc)
            self.add_doc(doc)

    # -----------------------------------------------------------------------

    def get_docs_sorted_by_newest(self) -> list:
        """Get documents sorted by date from the most recent to the oldest.

        Return the list of ImmutableDocument() instances sorted
        from the most recent to the oldest.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> sorted_docs = doc1.get_docs_sorted_by_newest()
        >>> for doc in sorted_docs:
        >>>     print(doc)
        >>> # The documents are printed from the most recent to the oldest

        :return: (list) The list of sorted documents

        """
        sorted_docs = sorted(self.__docs, key=lambda doc: doc.date, reverse=True)
        return [doc.to_immutable() for doc in sorted_docs]

    # -----------------------------------------------------------------------

    def get_docs_sorted_by_oldest(self) -> list:
        """Get documents sorted by date from the oldest to the most recent.

        Return the list of ImmutableDocument() instances sorted
        from the oldest to the most recent.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> sorted_docs = doc1.get_docs_sorted_by_oldest()
        >>> # The documents are printed from the oldest to the most recent
        >>> for doc in sorted_docs:
        >>>     print(doc)

        :return: (list) The list of sorted documents

        """
        sorted_docs = sorted(self.__docs, key=lambda doc: doc.date)
        return [doc.to_immutable() for doc in sorted_docs]

    # -----------------------------------------------------------------------

    def get_docs_sorted_by_most_viewed(self) -> list:
        """Get documents sorted by the number of views.

        Return the list of ImmutableDocument() instances sorted
        from the most viewed to the least viewed.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> sorted_docs = doc1.get_docs_by_most_viewed()
        >>> # The documents are printed from the most viewed to the least viewed
        >>> for doc in sorted_docs:
        >>>     print(doc)

        :return: (list) The sorted list of documents

        """
        sorted_docs = sorted(self.__docs, key=lambda doc: doc.downloads, reverse=True)
        return [doc.to_immutable() for doc in sorted_docs]

    # -----------------------------------------------------------------------

    def get_docs_sorted_by_least_viewed(self) -> list:
        """Get documents reversely sorted by the number of views.

        Return the list of ImmutableDocument() instances sorted
        from the least viewed to the most viewed.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> sorted_docs = doc1.get_docs_by_least_viewed()
        >>> for doc in sorted_docs:
        >>>     print(doc)

        :return: (list) The list of sorted documents

        """
        sorted_docs = sorted(self.__docs, key=lambda doc: doc.downloads)
        return [doc.to_immutable() for doc in sorted_docs]

    # -----------------------------------------------------------------------

    def filter_docs(self, filters, match_all: bool = False, out_filterset: bool = False):
        """Return the list of documents matching the given filters.

        Each filter is a tuple (filter function name, comparator name, [value1, value2, ...]).
        Applicable filter functions are "filename", "filetype", "author" and "date".

        :example:
        >>> manager = DocumentsManager('test_folder')
        >>> manager.collect_docs()
        >>> # Get all documents of Brigitte Bigi
        >>> manager.filter_docs(("author", "iexact", ["Brigitte Bigi"]))
        >>> # Get all PDF or TXT documents of Brigitte Bigi
        >>> _docs = manager.filter_docs(("author", "iexact", ["Brigitte Bigi"]), ("filetype", "iexact", ["pdf", "txt"]), match_all=True)
        >>> # Get all PDF or TXT documents of Brigitte Bigi or John Doe
        >>> _fdocs = manager.filter_docs(("author", "iexact", ["Brigitte Bigi", "John Doe"]), ("filetype", "iexact", ["pdf", "txt"]), match_all=True)

        :param filters: (list of tuple) List of filters to be applied on the documents.
        :param match_all: (bool) If True, returned documents must match all the given criteria
        :param out_filterset: (bool) If True, return the FilteredSet. If False, return a list of documents.
        :raises: ValueError: If a malformed filter.
        :raises: ValueError: If no value is provided in a filter.
        :raises: TypeError: invalid type for match_all parameter -- if used only
        :return: (list|FilteredSet) The list of documents matching the given criteria

        """
        doc_filter = DocumentsFilters(self.__docs)
        filtered_sets = list()
        cast_filters = self.__cast_filters(filters)

        # Apply each filter and append the result in a list of file's sets
        for f in cast_filters:
            # Apply the filter on the 1st value
            value = f[2][0]
            logging.info(" >>> filter.{:s}({:s}={!s:s})".format(f[0], f[1], value))
            files_set = getattr(doc_filter, f[0])(**{f[1]: value})
            #   - getattr() returns the value of the named attributed of object:
            #     it returns f.date if called with getattr(f, "date")
            #   - func(**{'x': '3'}) is equivalent to func(x='3')

            # Apply the filter on the next values
            for i in range(1, len(f[2])):
                value = doc_filter.cast_data(f[0], f[2][i])
                if "not" in f[1]:
                    logging.info(" >>>    & filter.{:s}({:s}={!s:s})".format(f[0], f[1], value))
                    files_set = files_set & getattr(doc_filter, f[0])(**{f[1]: value})
                else:
                    logging.info(" >>>    | filter.{:s}({:s}={!s:s})".format(f[0], f[1], value))
                    files_set = files_set | getattr(doc_filter, f[0])(**{f[1]: value})

            filtered_sets.append(files_set)

        # None of the documents is matching
        if len(filtered_sets) == 0:
            return list()
        # At least one document is matching
        files_set = doc_filter.merge_data(filtered_sets, match_all)
        if out_filterset is True:
            # Return the FilteredSet
            return files_set

        # Return the documents, sorted by date -- newest first
        return sorted(files_set, key=lambda doc: doc.date)

    # -----------------------------------------------------------------------
    # Operate on a specific document
    # -----------------------------------------------------------------------

    def get_doc_absolute_path(self, document: Document | ImmutableDocument) -> str:
        """Return the full filename to get access to the document.

        :param document: (Document | ImmutableDocument) The document to invalidate
        :return: (str) The full path of the document

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.invalidate_doc exception: No documents found."
                                 " Please run collect_docs() first")
        TypesDealer.check_types("DocumentsManager.invalidate_doc", [(document, (Document, ImmutableDocument))])

        # Compare the document given in parameter with his file_path or by the document itself
        doc = self.__find_doc(document)

        if doc is not None:
            return os.path.join(self.__absolute_path, self.__folder_path, doc.folder_name, doc.filename + "." + doc.filetype)
        return ""

    # -----------------------------------------------------------------------

    def get_doc_relative_path(self, document: Document | ImmutableDocument) -> str:
        """Return the filename with a relative path to get access to the document.

        :param document: (Document | ImmutableDocument) The document to invalidate
        :return: (str) The full path of the document

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.invalidate_doc exception: No documents found."
                                 " Please run collect_docs() first")
        TypesDealer.check_types("DocumentsManager.invalidate_doc", [(document, (Document, ImmutableDocument))])

        # Compare the document given in parameter with his file_path or by the document itself
        doc = self.__find_doc(document)

        if doc is not None:
            return os.path.join(self.__folder_path, doc.folder_name, doc.filename + "." + doc.filetype)
        return ""

    # -----------------------------------------------------------------------

    def invalidate_doc(self, document: Document | ImmutableDocument) -> None:
        """Delete a document of the disk and remove it of the managed ones.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # Assuming your_document is a document in the folder
        >>> doc1.invalidate_doc(your_document)

        :param document: (Document | ImmutableDocument) The document to invalidate
        :raises: ValueError: The document was not found
        :raises: AttributeError: No documents found. Please run collect_docs() first
        :raises: TypeError: Invalid document type

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.invalidate_doc exception: No documents found."
                                 " Please run collect_docs() first")
        TypesDealer.check_types("DocumentsManager.invalidate_doc", [(document, (Document, ImmutableDocument))])

        # Compare the document given in parameter with his file_path or by the document itself
        doc = self.__find_doc(document)

        if doc is not None:
            # Remove the document from the list
            self.__docs.remove(doc)
            # Delete the document file of the disk
            directory_path = os.path.join(self.__absolute_path, self.__folder_path, doc.folder_name)
            try:
                shutil.rmtree(directory_path)
                logging.info(f"Directory {directory_path} deleted.")
            # If the directory does not exist, ignore the error
            except Exception as e:
                logging.error(f"Directory {directory_path} not deleted: {e}")
        else:
            raise ValueError(f"DocumentsManager.invalidate_doc exception: Document {document.filename} not found.")

    # -----------------------------------------------------------------------

    def set_doc_description(self, document: Document | ImmutableDocument, description: str):
        """Set and save a description for a document.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> doc1.set_doc_description(your_document, "This is a description")

        :param document: (Document | ImmutableDocument) The document
        :param description: (str) The description to set
        :raises: AttributeError: No documents found. Please run collect_docs() first
        :raises: TypeError: Invalid document type

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.set_description exception: No documents found. "
                                 "collect_docs() should be called first.")
        TypesDealer.check_types("DocumentsManager.delete", [(document, (Document, ImmutableDocument))])

        doc = self.__find_doc(document)
        if doc is not None:
            if isinstance(doc, ImmutableDocument) is True:
                raise ValueError("Attempted to set description of an immutable document.")
            # Set the new description to the document
            doc.description = description
            # Save the description into the description file
            self.__save_description(doc)
        else:
            raise AttributeError(
                f"DocumentsManager.set_description exception: "
                f"Document {document.filename} not found.")

    # -----------------------------------------------------------------------

    def increment_doc_downloads(self, document: Document | ImmutableDocument) -> int:
        """Increment the number of downloads of a document.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> doc1.increment_doc_downloads(your_document)

        :param document: (Document | ImmutableDocument) The document
        :raises: AttributeError: Document not found.
        :raises: TypeError: Invalid document type
        :return: (int) New number of donwloads

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.increment_doc_downloads exception: Document not found. ")
        TypesDealer.check_types("DocumentsManager.increment_doc_downloads", [(document, (Document, ImmutableDocument))])

        doc = self.__find_doc(document)
        if doc is None:
            raise AttributeError(
                f"DocumentsManager.increment_doc_downloads exception: "
                f"Document {document.filename} not found.")
        if isinstance(doc, ImmutableDocument) is True:
            raise TypeError("Attempted to increment downloads of an immutable document.")

        # Increment the number of downloads into the document
        nb = doc.increment_downloads()
        # Save the new number into the downloads file
        self.__save_downloads(doc)
        return nb

    # -----------------------------------------------------------------------

    def save_doc(self, document: Document | ImmutableDocument):
        """Save a document.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # You can save the document in a different folder
        >>> doc1.save_doc(your_document, 'new_folder')
        >>> # Or in the folder with the DocumentsManager was initialized
        >>> doc1.save_doc(your_document)

        :param document: (Document | ImmutableDocument) The document
        :raises: TypeError: Invalid document type or folder path type
        :return: (bool) Success

        """
        # Create the folder to save the file
        folder_path = os.path.join(self.__absolute_path, self.__folder_path, document.folder_name)
        os.makedirs(folder_path, exist_ok=True)
        logging.debug("Created folder: {}".format(os.path.join(self.__absolute_path, self.__folder_path, document.folder_name)))

        file_path = self.get_doc_absolute_path(document)

        # Determine the appropriate mode to open the file.
        try:
            if isinstance(document.content, (bytes, bytearray)) is True:
                with open(file_path, "wb") as fp:
                    fp.write(document.content)
            else:
                with codecs.open(file_path, "w", "utf-8") as fp:
                    fp.write(document.content)

            # Save additional information.
            if os.path.exists(file_path) is True:
                self.__save_description(document)
                self.__save_downloads(document)
        except:
            shutil.rmtree(folder_path)
            raise

    # -----------------------------------------------------------------------

    def get_doc_content(self, document: Document | ImmutableDocument) -> str | bytes:
        """Get the content of a document.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # Assuming your_document is a document in the folder
        >>> doc1.get_doc_content(your_document)
        >>> print(your_document.content)

        :param document: (Document|ImmutableDocument) The document
        :raises: FileNotFoundError: The file was not found
        :raises: AttributeError: No documents found. Please run collect_docs() first
        :raises: TypeError: Invalid document type
        :return: (str|bytes|None) The content of the document

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.get_doc_content exception: No documents found. "
                                 "collect_docs() should be called first.")
        TypesDealer.check_types("DocumentsManager.get_doc_content", [(document, Document)])

        doc = self.__find_doc(document)
        content = ""
        if doc is not None:
            if len(doc.content) == 0:
                # the content has never been loaded. do it now.
                file_path = self.get_doc_absolute_path(doc)
                if os.path.exists(file_path) is True:
                    # The file has already been saved at least once
                    with open(file_path, 'r') as file:
                        content = file.read()
                    doc.content = content
                else:
                    logging.error(f"DocumentsManager.get_doc_content error: Document file path {file_path} not found. ")
            else:
                content = doc.content
        else:
            logging.error(f"DocumentsManager.get_doc_content error: Document {document.filename} not found. ")
        return content

    # -----------------------------------------------------------------------------------------------------------------

    def get_doc_description(self, document: Document | ImmutableDocument) -> str | None:
        """Get the description of a document.

        :example:
        >>> doc1 = DocumentsManager('test_folder')
        >>> doc1.collect_docs()
        >>> # Assuming your_document is a document in the folder
        >>> doc1.get_doc_description(your_document)
        >>> print(your_document.description)

        :param document: (Document | ImmutableDocument) The document
        :raises: FileNotFoundError: The file was not found
        :raises: AttributeError: No documents found. Please run collect_docs() first
        :raises: TypeError: Invalid document type
        :return: (str|None) The description of the document

        """
        if len(self.__docs) == 0:
            raise AttributeError("DocumentsManager.get_doc_description exception: No documents found. "
                                 "collect_docs() should be called first.")
        TypesDealer.check_types("DocumentsManager.get_doc_description", [(document, (Document, ImmutableDocument))])

        doc = self.__find_doc(document)
        if doc is not None:
            return doc.description

        raise ValueError(f"DocumentsManager.get_doc_description exception: Document {document.filename} not found.")

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __read_info(self, folder_name: str, fn: str) -> str:
        """Return the content of the given file in the given folder.

        :param folder_name: (str) The name of the folder
        :param fn: (str) The name of the file
        :return: (str) The content of the file

        """
        info = ""
        file_path = os.path.join(self.__absolute_path, self.__folder_path, folder_name, fn)
        if os.path.exists(file_path) is True:
            with codecs.open(file_path, "r", encoding="utf-8") as file:
                info = file.read().strip()
        return info

    # -----------------------------------------------------------------------

    def __save_description(self, document: Document | ImmutableDocument):
        """Save description into its file.

        :param document: (Document | ImmutableDocument) The document

        """
        self.__save_info(document.folder_name, whakerkit.sg.DESCRIPTION_FILENAME, document.description)

    # -----------------------------------------------------------------------

    def __save_downloads(self, document: Document | ImmutableDocument):
        """Save downloads into its file.

        :param document: (Document | ImmutableDocument) The document

        """
        self.__save_info(document.folder_name, whakerkit.sg.DOWNLOADS_FILENAME, str(document.downloads))

    # -----------------------------------------------------------------------

    def __save_info(self, folder_name, filename, content):
        """Save the content into the given file of the specified folder.

        """
        directory_path = os.path.join(self.__absolute_path, self.__folder_path, folder_name)
        if os.path.exists(directory_path) is False:
            raise FileNotFoundError(f"The directory {directory_path} does not exist.")
        try:
            destination = os.path.join(directory_path, filename)
            with codecs.open(destination, "w", "utf-8") as file:
                file.write(content)
            logging.debug(f"Saved information into file: {destination}")
        except Exception as e:
            raise Exception(f"Information of document {folder_name} not saved: {e}")

    # -----------------------------------------------------------------------

    def __find_doc(self, document: Document | ImmutableDocument) -> Document | None:
        """Search for a document in the list of stored documents.

         Find the instance of Document which is matching the given document
         in the list of stored docs.i If it finds a matching document, it
         returns the document instance; otherwise, it returns None.

        :param document: (Document | ImmutableDocument) The document to find
        :return: (Document | None) The document found or None if not found or invalid

        """
        # Two docs are equal if same author, filename, filetype and date.
        # See Document.__eq__ for details.
        return next((doc for doc in self.__docs if doc == document), None)

    # -----------------------------------------------------------------------

    @staticmethod
    def __immutable_to_document(idoc: ImmutableDocument) -> Document:
        """Convert an ImmutableDocument into a Document."""
        return Document(idoc.author, idoc.filename + "." + idoc.filetype, idoc.date,
                        content=idoc.content,
                        description=idoc.description,
                        downloads=idoc.downloads)

    # -----------------------------------------------------------------------

    def __cast_filters(self, filters: list) -> list:
        """Return the value-typed of given filters.

        :param filters: (list of tuple) List of filters to be applied on the documents.
        :raises: ValueError: If a malformed filter.
        :raises: ValueError: If an invalid field is provided in a filter.
        :return: (list of tuple) List of filters to be applied on the documents with typed values.

        """
        cast_filters = list()
        doc_filter = DocumentsFilters(self.__docs)

        # Apply each filter and append the result in a list of file's sets
        for f in filters:
            if isinstance(f, (list, tuple)) and len(f) == 3:
                if None in f or any(len(f[i]) == 0 for i in range(len(f))):
                    raise ValueError("Invalid field defined for filter {:s}".format(str(f)))
                casted_values = list()
                for value in f[2]:
                    casted_values.append(doc_filter.cast_data(f[0], value))

                cast_filters.append((f[0], f[1], casted_values))
            else:
                raise ValueError("Filter must have 3 arguments: function, comparator, value."
                                 "Got {:d} instead.".format(len(f)))

        return cast_filters

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __len__(self):
        return len(self.__docs)

    # -----------------------------------------------------------------------

    def __iter__(self):
        for doc in self.__docs:
            yield doc.to_immutable()

    # -----------------------------------------------------------------------

    def __contains__(self, document):
        # do not un-necessarily browse through the documents
        if isinstance(document, (Document, ImmutableDocument)) is False:
            return False
        # compare given document to each of ours with '=='.
        # allows to return true if all(author, filename, date, filetype) are equals
        for doc in self.__docs:
            if doc == document:
                return True
        return False
