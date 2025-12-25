# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.components.book.py
:author: Brigitte Bigi
:contributor: Florian Lopitaux
:contact: contact@sppas.org
:summary: Class to create a custom book HTMLNode.

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

import logging

from whakerpy import HTMLNode
from whakerpy import HTMLHeadNode
from whakerpy import HTMLNavNode

# -----------------------------------------------------------------------

CSS_STYLE = """
:root {
    --toc-width: 18rem;
}

"""

JS_VALUE = """
window.Wexa.onload.addLoadFunction(() => {
    let book = new Book("%id%");
    
    book.delete_html_tags("h1", "h2", "h3", "h4");
    book.add_html_tags("%tags%");
    
    book.fill_table(%bool%);
});

"""

# -----------------------------------------------------------------------


class BookNode(HTMLNavNode):
    """Create the HTMLNode for a custom book based on Whakerexa.

    """

    REQUIRED = ["book.css", "book.js"]


    def __init__(self, parent_id: str, title: str, head: HTMLHeadNode, id_main_content: str = "main-content"):
        """Initialize the table of contents and return an instance of Book.

        :param parent_id: (str) the identifier of the parent
        :param title: (str) the title of the book put in the top of the table of contents
        :param head: (HTMLHeadNode) the head node to put the script to fill the table content of headings
        :param id_main_content: (str) Optional, the id (id attribute in the html) of the element
                                where searched the headings, by default is set to 'main-content'.

        """
        super(BookNode, self).__init__(parent_id)
        self.set_attribute("id", "nav-content")
        self.set_attribute("class", "side-nav")

        self.__head = head
        self.__headings = id_main_content
        self.__html_tags = "h1, h2, h3, h4"
        self.__only_numerate_headings = True

        self.__create(title)

    # -----------------------------------------------------------------------
    # GETTERS
    # -----------------------------------------------------------------------

    def get_title(self) -> str:
        """Get the title of the book put on the top of the table of contents.

        :return: (str) the title value

        """
        return self.get_child("toc-title").get_value()

    # -----------------------------------------------------------------------

    def is_only_numerate_headings(self) -> bool:
        """Get the boolean value to know if we detect all headings or just numerated with 'ssection' headings.

        :return: (bool) the boolean value

        """
        return self.__only_numerate_headings

    # -----------------------------------------------------------------------
    # SETTERS
    # -----------------------------------------------------------------------

    def set_tile(self, title: str) -> None:
        """Set teh title of the book put on the top of the table of contents.

        :param title: the title value

        """
        self.get_child("toc-title").set_value(title)

    # -----------------------------------------------------------------------

    def set_headings_container(self, id_container: str) -> None:
        """Set the id (html element id not node identifier) of the html element that contains our headings.

        :param id_container: (str) the id of the element

        """
        self.__headings = id_container
        self.__insert_script()

    # -----------------------------------------------------------------------

    def detect_only_numerate_headings(self, value: bool) -> None:
        """Set the boolean value to know if the book detect only numerate headings from 'ssection'.

        :param value: (bool) the boolean value set

        """
        self.__only_numerate_headings = value
        self.__insert_script()

    # -----------------------------------------------------------------------

    def add_html_tags(self, *tags: str) -> None:
        """Add html tags to detect when we fill the book.

        :param tags: (str [0, n]) the html tags that the book has to detect

        """
        for current_tag in tags:
            if current_tag not in self.__html_tags:
                self.__html_tags += f", {current_tag}"
            else:
                logging.warning(f"HTML tag '{current_tag}' already in the list : {self.__html_tags}")

    # -----------------------------------------------------------------------

    def delete_html_tags(self, *tags: str) -> None:
        """Delete given html tags.

        :param tags: (str) (0, n) the html tags to delete
        """
        for current_tag in tags:
            if current_tag in self.__html_tags:
                self.__html_tags.replace(f", {current_tag}", "")
            else:
                logging.warning(f"HTML tag '{current_tag}' not in the list : {self.__html_tags}")

    # -----------------------------------------------------------------------
    # PUBLIC METHODS
    # -----------------------------------------------------------------------

    def add_link(self, url: str) -> None:
        """Insert a link to the table of contents before the headings.

        :param url: the url where the link redirect

        """
        link = HTMLNode(self.identifier, None, "a", value=url, attributes={
            'class': "external-link",
            'href': url
        })

        self.insert_child(1, link)

    # -----------------------------------------------------------------------
    # PRIVATE METHODS
    # -----------------------------------------------------------------------

    def __insert_script(self) -> None:
        """Insert the script in the head to fill the table with headings.

        """
        self.__head.remove_child("book-script")

        format_js_value = JS_VALUE.replace("%id%", self.__headings)
        format_js_value = format_js_value.replace("%tags%", self.__html_tags)
        format_js_value = format_js_value.replace("%bool%", str(self.__only_numerate_headings).lower())
        book_script = HTMLNode(self.__head.identifier, "book-script", "script", value=format_js_value,
                               attributes={'type': "module"})

        self.__head.append_child(book_script)

    # -----------------------------------------------------------------------

    def __create(self, title: str) -> None:
        """Create the static contents of the table of contents.

        :param title: (str) the title of the book put in the top of the table of contents

        """
        book_style = HTMLNode(self.__head.identifier, "book-style", "style", value=CSS_STYLE)
        self.__head.remove_child("book-style")  # if we instantiate multiple book in the same page (horrible !)
        self.__head.append_child(book_style)

        self.__insert_script()

        h1 = HTMLNode(self.identifier, "toc-title", "h1", value=title)
        h2 = HTMLNode(self.identifier, None, "h2", value="Table Of Contents")
        ul = HTMLNode(self.identifier, None, "ul", attributes={'id': "toc"})

        self.append_child(h1)
        self.append_child(h2)
        self.append_child(ul)
