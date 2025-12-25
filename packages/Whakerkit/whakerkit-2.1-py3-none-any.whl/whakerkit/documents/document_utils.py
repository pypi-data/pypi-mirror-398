"""
:filename: whakerkit.documents.document_utils.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Utilities for managing documents

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
import os
import datetime

import whakerkit
from ..config.typesdealer import TypesDealer

# ---------------------------------------------------------------------------


class DocumentUtils:

    @staticmethod
    def get_filetype(filename: str) -> str:
        """Get the filetype of a document.

        If filename is an extension (like '.txt'), treat it as an extension without a name.
        If there is no dot or only an initial dot without extension, return an empty string.

        :param filename: (str) The name of the document
        :return: (str) The filetype of the document, or an empty string if none is found.

        """
        if filename.startswith('.') and filename.count('.') == 1:
            return filename[1:]
        ext = os.path.splitext(filename)[1]
        return ext.lstrip('.')

    # -----------------------------------------------------------------------

    @staticmethod
    def get_folder_name(author: str, filename: str,
                        date: datetime.datetime | datetime.date | None,
                        filetype: str | None) -> str:
        """Generate a folder name string by combining the given parameters.

        :param author: (str)
        :param filename: (str)
        :param date: (datetime | date | None)
        :param filetype: (str | None)
        :return: (str) A name of folder from given parameters

        """
        sep = whakerkit.sg.FOLDER_NAME_SEPARATOR
        return sep.join(
            (DocumentUtils.format_author(author),
             DocumentUtils.date_to_str(date),
             DocumentUtils.format_filetype(filetype),
             DocumentUtils.format_filename(filename)),
            )

    # -----------------------------------------------------------------------

    @staticmethod
    def format_author(author: str) -> str:
        """Return the formatted given author name.

        :param author: (str) The author to be formatted
        :return: (str) The formatted filetype or extension

        """
        author = TypesDealer.cast_types(author, str)
        author = author.replace(whakerkit.sg.FOLDER_NAME_SEPARATOR, whakerkit.sg.FIELDS_NAME_SEPARATOR)
        return TypesDealer.clear_whitespace(
            TypesDealer.clear_string(author, whakerkit.sg.INVALID_CHARS_FOR_FOLDERS), whakerkit.sg.FIELDS_NAME_SEPARATOR)

    # -----------------------------------------------------------------------

    @staticmethod
    def format_filename(filename: str) -> str:
        """Return the formatted basename of the given file.

        :param filename: (str) The name of the document
        :return: (str) The formatted basename of the document

        """
        filename = TypesDealer.cast_types(filename, str)
        base_filename, _ = os.path.splitext(filename)
        base_filename = base_filename.replace(whakerkit.sg.FOLDER_NAME_SEPARATOR, whakerkit.sg.FIELDS_NAME_SEPARATOR)
        return TypesDealer.clear_whitespace(
                TypesDealer.clear_string(
                    base_filename, whakerkit.sg.INVALID_CHARS_FOR_FIELDS), whakerkit.sg.FIELDS_NAME_SEPARATOR)

    # -----------------------------------------------------------------------

    @staticmethod
    def format_date(date: datetime.datetime | datetime.date | None) -> datetime.date:
        """Return the formatted given date.

        :param date: (datetime.datetime or datetime.date) The date to be formatted
        :return: (date) The formatted given date

        """
        if isinstance(date, datetime.datetime) is True:
            return datetime.date(date.year, date.month, date.day)
        elif isinstance(date, datetime.date) is True:
            return date

        # Invalid parameter or None
        date = datetime.datetime.now()
        return datetime.date(date.year, date.month, date.day)

    # -----------------------------------------------------------------------

    @staticmethod
    def format_filetype(filetype: str) -> str:
        """Return the formatted given file type.

        :param filetype: (str) The filetype or extension to be formatted
        :return: (str) The formatted filetype or extension

        """
        filetype = str(filetype)
        if filetype.startswith('.'):
            filetype = filetype[1:]
        return filetype.lower()

    # -----------------------------------------------------------------------

    @staticmethod
    def format_description(description: str) -> str:
        """Return the formatted given description.

        :param description: (str) The description to be formatted
        :return: (str) The formatted description

        """
        return TypesDealer.cast_types(description, str)

    # -----------------------------------------------------------------------

    @staticmethod
    def str_to_date(entry: str) -> datetime.date:
        """Return the date matching the given string.

        :param entry: (str) The date to be formatted
        :return: (datetime.date) Date matching the given entry

        """
        TypesDealer.check_types("", [(entry, str)])
        entry = entry.replace(whakerkit.sg.FIELDS_NAME_SEPARATOR, "-")
        return DocumentUtils.format_date(datetime.datetime.strptime(entry, "%Y-%m-%d"))

    # -----------------------------------------------------------------------

    @staticmethod
    def date_to_str(date: datetime.datetime | datetime.date | None) -> str:
        """Return the stringified date matching the given entry.

        :param date: (datetime.datetime | datetime.date | None) The date to be formatted
        :return: (str) The string representing the given date

        """
        if isinstance(date, (datetime.datetime, datetime.date)) is False:
            date = datetime.datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        return date_str.replace("-", whakerkit.sg.FIELDS_NAME_SEPARATOR)
