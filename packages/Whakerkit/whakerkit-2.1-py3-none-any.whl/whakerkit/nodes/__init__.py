# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.nodes.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org

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

from .head_node import WhakerKitHeadNode
from .nav_node import WhakerKitNavNode
from .accessibility import WhakerKitAccessibilityNavNode
from .doc import DOC_FIELDS
from .docs_node import ToggleColumnsNode
from .docs_node import DocumentsNode
from .footer_node import WhakerKitFooterNode
from .card_node import WhakerKitDocumentCardNode
from .header_node import WhakerKitHeaderNode
from .login_node import WhakerKitLoginNode
from .doc_aside_node import WhakerKitDocAsideNode
from .docs_node import DocumentsNode
from .search_node import WhakerKitSearchNode
from .filter_node import WhakerKitFilterNode

__all__ = (
    "WhakerKitHeadNode",
    "WhakerKitNavNode",
    "WhakerKitDocumentCardNode",
    "ToggleColumnsNode",
    "DocumentsNode",
    "WhakerKitFooterNode",
    "WhakerKitHeaderNode",
    "WhakerKitLoginNode",
    "WhakerKitDocAsideNode",
    "DocumentsNode",
    "WhakerKitSearchNode",
    "WhakerKitFilterNode"
)
