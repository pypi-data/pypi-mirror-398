# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.doc.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary; Data class for properties of a document.

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

from dataclasses import dataclass

from whakerkit import get_msg

# ---------------------------------------------------------------------------


MSG_NAME = "File name"
MSG_AUTHOR = "Depositor"
MSG_TYPE = "Type"
MSG_DATE = "Date"
MSG_DESCRIPTION = "Description"
MSG_DOWNLOADS = "DLs"

# ---------------------------------------------------------------------------


@dataclass
class WhakerKitDocumentProperties:
    """Represents properties of document's fields.

    List of attributes:
    
    - label (str): The display message for the field, describing its content (e.g., "Author", "Date").
    - is_sortable (bool): Specifies if the field can be sorted in the document listing.
    - is_toggable (bool): Indicates whether the field can be toggled to show/hide the field.
    - is_hidden (bool): Defines whether the field is hidden to the user by default.
    
    """
    label: str
    is_sortable: bool
    is_toggable: bool
    is_hidden: bool

# ---------------------------------------------------------------------------
# Sorted dictionary describing the document fields:
#  - key = identifier
#  - value = DocumentProperties(MSG, is_sortable, is_toggable, is_hidden)


DOC_FIELDS = {
    "filename": WhakerKitDocumentProperties(get_msg(MSG_NAME), True, True, False),
    "author": WhakerKitDocumentProperties(get_msg(MSG_AUTHOR), True, True, False),
    "date": WhakerKitDocumentProperties(get_msg(MSG_DATE), True, True, False),
    "filetype": WhakerKitDocumentProperties(get_msg(MSG_TYPE), True, True, False),
    "description": WhakerKitDocumentProperties(get_msg(MSG_DESCRIPTION), False, True, True),
    "downloads": WhakerKitDocumentProperties(get_msg(MSG_DOWNLOADS), False, True, True),
}
