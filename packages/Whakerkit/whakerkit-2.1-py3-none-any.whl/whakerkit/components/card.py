# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.components.card.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Class to create a custom card HTMLNode.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io
.. _This file was originally part of SPPAS  - by Brigitte Bigi, CNRS.
    Integrated into WhakerKit 1.2.

    Copyright (C) 2011-2025  Brigitte Bigi, CNRS
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

from whakerpy.htmlmaker import HTMLNode
from whakerpy.htmlmaker import NodeIdentifierError

# -----------------------------------------------------------------------


class CardNode(HTMLNode):
    """Create the HTMLNode for a custom card based on Whakerexa.

    """

    REQUIRED = ["layout.css"]

    def __init__(self, parent_id: str, identifier: str, is_full_card: bool = False):
        """Initialize a new instance of a Card object.

        :param parent_id: (str) the identifier of the parent node
        :param identifier: (str) the identifier of the card
        :param is_full_card: (bool) optional, if the card is a "full-card" or normal, false by default.

        """
        super(CardNode, self).__init__(parent_id, identifier, "article")
        self.set_attribute("class", "card")
        if is_full_card:
            self.add_attribute("class", "full-card")

        self.__header_identifier = f"card-{self.identifier}-header"
        self.__main_identifier = f"card-{self.identifier}-main"
        self.__footer_identifier = f"card-{self.identifier}-footer"

        self.__create()

    # -----------------------------------------------------------------------
    # GETTERS & SETTERS
    # -----------------------------------------------------------------------

    def get_card_header(self) -> HTMLNode:
        """Get the card->header element node.

        :return: (HTMLNode) Card header node element

        """
        return self.get_child(self.__header_identifier)

    def set_card_header(self, header: HTMLNode) -> None:
        """Replace the current card->header node by the given one.

        :param header: (HTMLNode) the header of the card

        :Raises: NodeIdentifierError: if the identifier of the given header is not "card-{card-identifier}-header"

        """
        if header.identifier != self.__header_identifier:
            raise NodeIdentifierError(self.__header_identifier, header.identifier)

        header.set_parent(self.identifier)
        self.remove_child(self.__header_identifier)
        self.append_child(header)

    card_header = property(get_card_header, set_card_header)

    # -----------------------------------------------------------------------

    def get_card_main(self) -> HTMLNode:
        """Get the card->main element node.

        :return: (HTMLNode) Card main node element

        """
        return self.get_child(self.__main_identifier)

    def set_card_main(self, main: HTMLNode) -> None:
        """Replace the current card->main node by the given one.

        :param main: (HTMLNode) the main of the card

        :Raises: NodeIdentifierError: if the identifier of the given main is not "card-{card-identifier}-main"

        """
        if main.identifier != self.__main_identifier:
            raise NodeIdentifierError(self.__main_identifier, main.identifier)

        main.set_parent(self.identifier)
        self.remove_child(self.__main_identifier)
        self.append_child(main)

    card_main = property(get_card_main, set_card_main)

    # -----------------------------------------------------------------------

    def get_card_footer(self) -> HTMLNode:
        """Get the card->footer element node.

        :return: (HTMLNode) Card footer node element

        """
        return self.get_child(self.__footer_identifier)

    def set_card_footer(self, footer: HTMLNode) -> None:
        """Replace the current card->footer node by the given one.

        :param footer: (HTMLNode) the footer of the card

        :Raises: NodeIdentifierError: if the identifier of the given footer is not "card-{card-identifier}-footer"

        """
        if footer.identifier != self.__footer_identifier:
            raise NodeIdentifierError(self.__footer_identifier, footer.identifier)

        footer.set_parent(self.identifier)
        self.remove_child(self.__footer_identifier)
        self.append_child(footer)

    card_footer = property(get_card_footer, set_card_footer)

    # -----------------------------------------------------------------------
    # PRIVATE METHODS
    # -----------------------------------------------------------------------

    def __create(self) -> None:
        """Create the static contents of the card (header, main, footer).

        """
        header = HTMLNode(self.identifier, self.__header_identifier, "header")
        self.append_child(header)

        main = HTMLNode(self.identifier, self.__main_identifier, "main")
        self.append_child(main)

        footer = HTMLNode(self.identifier, self.__footer_identifier, "footer")
        self.append_child(footer)
