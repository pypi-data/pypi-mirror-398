"""
:filename: whakerkit.documents.document.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Represents a document and its metadata.

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
import datetime

import whakerkit
from ..config import TypesDealer

from .document_utils import DocumentUtils

# ---------------------------------------------------------------------------


class ImmutableDocument:
    """Ensure instances become immutable after their creation.

    This is achieved by using _is_frozen attribute to True after the instance
    is created, preventing further modifications to its attributes.

    :example:
    >>> doc = ImmutableDocument(
    >>>           author="Alice",
    >>>           filename="Doc1.txt",
    >>>           content="a cool content",
    >>>           date=datetime.date(2024, 1, 1),
    >>>           filetype="txt")
    >>> print(doc.author)
    "Alice"
    >>> doc.author = "Bob"  # Raises AttributeError
    >>> del doc.author  # Raises AttributeError

    """

    def __init__(self, author: str,
                 filename: str,
                 date: datetime.date | datetime.datetime | None = None,
                 content: str | bytes = "",
                 description: str = "",
                 downloads: int = 0):
        # Temporarily allow setting attributes
        self._is_frozen = False

        # Set members
        self.author = DocumentUtils.format_author(author)
        self.content = content
        self.date = date
        self.description = description
        self.filename = DocumentUtils.format_filename(filename)
        self.filetype = DocumentUtils.get_filetype(filename)
        self.downloads = downloads

        # Freeze the instance
        self._is_frozen = True

    # -----------------------------------------------------------------------

    def get_folder_name(self) -> str:
        """Return the name of the folder in which the document is stored.

        The folder_name can be used for both:

        - an identifier for the document, and
        - get information about the document: author, filename, date and filetype

        """
        return DocumentUtils.get_folder_name(self.author, self.filename, self.date, self.filetype)

    folder_name = property(get_folder_name, None)

    def to_immutable(self) -> ImmutableDocument:
        return self

    # -----------------------------------------------------------------------

    def __setattr__(self, key, value):
        """Override to prevent any attribute setter."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__setattr__(key, value)

    def __delattr__(self, key):
        """Override to prevent any attribute deletion."""
        if getattr(self, "_is_frozen", False):
            raise AttributeError(f"{self.__class__.__name__} object is immutable")
        super().__delattr__(key)

    def __str__(self):
        return f"ImmutableDocument({self.author}, {self.filename}, {self.date}, {self.filetype})"

    def __repr__(self):
        return (f"ImmutableDocument(author={self.author}, filename={self.filename}, date={self.date}, "
                f"filetype={self.filetype})")

# ---------------------------------------------------------------------------


class Document:
    """Represent a file that will be uploaded to a server.

    It is designed to maintain metadata associated with the document.
    Logging should  be enabled to get some messages.

    :example:
    >>> # Create a new Document instance with all information
    >>> doc = Document("Alice", "Doc1.txt", content="a cool content",
    >>>                date=datetime(2024, 1, 1), filetype="txt")

  """

    def __init__(self, author: str,
                 filename: str,
                 date: datetime.date | datetime.datetime | None = None,
                 content: str | bytes = "",
                 description: str = "",
                 downloads: int = 0):
        """Initialize the document with the provided parameters.

        When the document is created, it is saved in a folder with the following format:
        author_date_filetype_filename

        :Example:
        >>> # Create a document without the extension in the filename (default: txt):
        >>> doc = Document("Alice", "Doc1", "Your_content", date=datetime.datetime(2023, 1, 1))
        >>> # Create a document with the extension in the filename:
        >>> doc2 = Document("Alice", "Doc1.txt", "Your_content", date=datetime.date(2023, 1, 1))
        >>> # Create a document without a date and filetype:
        >>> doc1 = Document("Alice", "Doc1", "Your_content")

        :param filename: (str) The name of the file provided with the extension
        :param author: (str) The author of the file
        :param content: (str) The content of the file (optional)
        :param date: (datetime|date) The date of the file (optional) (default: today)
        :param description: (str) The description of the file (optional)

        :raises: ValueError: if the filename is too short
        :raises: TypeError: if the parameters are not in the correct format

        """
        # Check if the filename is at least 4 characters long
        if len(filename) < whakerkit.sg.MIN_FILE_NAME_LENGTH:
            raise ValueError("Document.__init__: filename must be at least 4 characters long.")
        if len(author) < 1 or len(filename) < 1:
            raise ValueError("Document.__init__: author and filename must be at least 1 character long.")
        # Check if the parameters are in the correct format and type
        TypesDealer.check_types("Document.__init__", [(author, str), (filename, str), (description, (str, type(None)))])
        TypesDealer.check_types("Document.__init__", [(content, (str, bytes))])
        TypesDealer.check_types("Document.__init__", [(downloads, int)])
        if date is not None:
            TypesDealer.check_types("Document.__init__", [(date, (datetime.datetime, datetime.date))])

        # Format required fields
        self.__author = DocumentUtils.format_author(author)
        self.__filename = DocumentUtils.format_filename(filename)
        self.__filetype = DocumentUtils.get_filetype(filename)

        # Declare optional fields
        self.__date = DocumentUtils.format_date(date)
        self.__downloads = downloads
        self.__content = ""
        self.__description = ""

        # Set optional fields
        self.set_description(description)
        self.set_content(content)

    # -----------------------------------------------------------------------
    # Getters & Setters
    # -----------------------------------------------------------------------

    def to_immutable(self) -> ImmutableDocument:
        """Return an immutable copy of the document.

        Creates and returns an immutable copy of the current Document instance.
        This ensures that the returned document cannot be modified, preserving
        its state at the time of the method call.

        """
        return ImmutableDocument(
            author=self.__author,
            filename=self.__filename + "." + self.__filetype,
            content=self.__content,
            date=self.__date,
            description=self.__description,
            downloads=self.__downloads
        )

    # -----------------------------------------------------------------------

    def get_author(self) -> str:
        """Return the author of the document."""
        return self.__author

    author = property(get_author, None)

    # -----------------------------------------------------------------------

    def get_filename(self) -> str:
        """Return the filename of the document."""
        return self.__filename

    filename = property(get_filename, None)

    # -----------------------------------------------------------------------

    def get_filetype(self) -> str:
        """Return the filetype of the document.

        The filetype is the extension in lower-case and without the dot.

        """
        return self.__filetype

    filetype = property(get_filetype, None)

    # -----------------------------------------------------------------------

    def get_date(self) -> datetime.datetime | datetime.date | None:
        """Return the date associated to the document."""
        return self.__date if self.__date is not None else None

    date = property(get_date, None)

    # -----------------------------------------------------------------------

    def get_description(self) -> str:
        """Return the description of the document.

        :return: The description of the document or None if undefined

        """
        return self.__description

    # -----------------------------------------------------------------------

    def set_description(self, description: str):
        """Set the description of the document with no size limit.

        :param description: (str) The description of the document

        """
        TypesDealer.check_types("Document.set_description", [(description, str)])
        self.__description = description

    description = property(get_description, set_description)

    # -----------------------------------------------------------------------

    def get_folder_name(self) -> str:
        """Return the name of the folder in which the document is stored.

        The folder_name can be used for both:

        - an identifier for the document, and
        - get information about the document: author, filename, date and filetype

        """
        return DocumentUtils.get_folder_name(self.__author, self.__filename, self.__date, self.__filetype)

    folder_name = property(get_folder_name, None)

    # -----------------------------------------------------------------------

    def get_downloads(self) -> int:
        """Return the number of times the document was downloaded or 0.

        :return: (int) The number of downloads or -1 if error

        """
        return self.__downloads

    downloads = property(get_downloads, None)

    # -----------------------------------------------------------------------

    def get_content(self) -> str | bytes | None:
        """Return the content of the document.

        :return: (str|bytes|None) The content of the document

        """
        return self.__content

    # -----------------------------------------------------------------------

    def set_content(self, content: str | bytes):
        """Set the content of the document.

        :param content: (str) The content of the document

        """
        TypesDealer.check_types("Document.set_content", [(content, (str, bytes))])
        self.__content = content

    content = property(get_content, set_content)

    # -----------------------------------------------------------------------
    # Workers
    # -----------------------------------------------------------------------

    def increment_downloads(self) -> int:
        """Increment the number of downloads of the document."""
        self.__downloads += 1
        return self.__downloads

    # -----------------------------------------------------------------------

    @staticmethod
    def create_document_by_folder_name(folder_name: str, description: str = "", downloads: int = 0) -> ImmutableDocument:
        """Create an ImmutableDocument().

        :param folder_name: (str) Name of the document folder
        :param description: (str) The description of the document
        :param downloads: (int) The number of downloads of the document
        :raises: TypeError: An invalid given parameter
        :raises: ValueError: Invalid folder_name format
        :return: (ImmutableDocument) An instance created from the given folder name

        """
        TypesDealer.check_types("Document.get_document_by_folder_name", [(folder_name, str)])
        array = folder_name.split(whakerkit.sg.FOLDER_NAME_SEPARATOR)
        if len(array) > 4:
            raise ValueError("Expected a folder name with at least 4 fields "
                             "(author, date, filename, filetype) "
                             "separated by '{:s}'. Got {:d} fields instead."
                             "".format(whakerkit.sg.FOLDER_NAME_SEPARATOR, len(array)))

        return ImmutableDocument(
            array[0],
            array[3] + "." + array[2],
            date=DocumentUtils.str_to_date(array[1]),
            description=description,
            downloads=downloads)

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        return f"Document({self.get_author()}, {self.filename}, {self.date}, {self.__filetype})"

    def __repr__(self):
        return (f"Document(author={self.get_author()}, filename={self.filename}, date={self.date}, "
                f"filetype={self.__filetype})")

    def __eq__(self, other):
        """Check equality of two documents.

        Checks if two Document instances are equal by comparing their author,
        filename, filetype, and date.

        :param other: (Document) The document to be compared
        :return: (bool) True if the two documents are equal, False otherwise

        """
        if self is other:
            return True
        if isinstance(other, (Document, ImmutableDocument)) is True:
            return (self.__author == other.author and
                    self.__filename == other.filename and
                    DocumentUtils.date_to_str(self.__date) == DocumentUtils.date_to_str(other.date) and
                    self.__filetype == other.filetype)

        return False
