# -*- coding: UTF-8 -*-
"""
:filename: py.responses.stats_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system for the statistics page.

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
import os
import random
import ast

from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg

from .base import get_base_response_class  # WhakerKitResponse or Custom

# ---------------------------------------------------------------------------


MSG_TITLE_INDEX = "Consultations"
MSG_TITLE_HOME = "Website visit frequency"
MSG_TITLE_SEE_LOGS = "View logs"
MSG_TITLE_SEE_FREQ = "Number of accesses to HTML pages"
MSG_FREQ_OVERALL = "Overall view"
MSG_FREQ_DETAILS = "Monthly visits per page"
MSG_TITLE_SEE_FILTERS = "Document filters"
MSG_FILTERS_VALID = "Filters that found documents"
MSG_FILTERS_INVALID = "Filters that did not find documents"

# not translated yet:
MSG_EXPAND_FOR_CONTENT = "Déplier pour consulter le contenu du fichier {entry} ({content_len}) lignes)"
MSG_PAGE_SENT = "Page envoyée par le serveur"
MSG_OCC = "Occurrences"

# ---------------------------------------------------------------------------


def hex_code_colors():
    """Return a random color which is ok for light or black theme."""
    a = hex(random.randrange(96, 196))
    b = hex(random.randrange(96, 196))
    c = hex(random.randrange(96, 196))
    a = a[2:]
    b = b[2:]
    c = c[2:]
    if len(a) < 2:
        a = "0" + a
    if len(b) < 2:
        b = "0" + b
    if len(c) < 2:
        c = "0" + c
    z = a + b + c
    return "#" + z.upper()

# ---------------------------------------------------------------------------


class StatsResponse(get_base_response_class()):
    """The bake system for the website frequency of use page.

    It analyzes the wsgi.log file and draw some statistics.

    """

    def __init__(self):
        """Create the response for the index page.

        The body->main of this page is created fully dynamically, there's no
        file to get content from.

        """
        super(StatsResponse, self).__init__(name=None, title=get_msg(MSG_TITLE_INDEX))
        self.__logs = list()

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events: (dict) the posted events
        :param kwargs: (dict) the keyword arguments
        :return: (bool) True to bake the page, False otherwise

        """
        logging.debug(f"StatsResponse._process_events: {events.keys()}.")
        # HTTP status
        self._status.code = 200
        return True

    # -----------------------------------------------------------------------

    def create(self):
        """Override. Create the page tree.

        Set page name and add required js in the tree->head.

        """
        get_base_response_class().create(self)
        self.set_pagename("consultations.html")

    # -----------------------------------------------------------------------

    def _bake(self) -> None:
        """Create the dynamic content in the body->main of the page.

        """
        # Page main title -- <h1> element
        h1 = self._htree.element("h1")
        h1.set_value(get_msg(MSG_TITLE_HOME))

        # Load the logs
        self.load_and_view_logs()

        # Page views -- overall & month
        self.pages_frequencies()

        # Applied Filters
        self.applied_filters()

    # -----------------------------------------------------------------------

    def load_and_view_logs(self):
        """Fill-in the list of log contents and add notes to see the contents.

        """
        h2_logs = self._htree.element("h2")
        h2_logs.set_value(get_msg(MSG_TITLE_SEE_LOGS))
        # Iterate over all files. Load any file ending by ".log"
        for entry in os.listdir(whakerkit.sg.base_dir):
            if entry.endswith(".log") is True:
                with open(whakerkit.sg.base_dir + entry, "r", encoding="utf-8") as f:
                    content = "\n".join(f.readlines())
                    self.__logs.append(content)
                    content = content.replace("<", "&lt;").replace(">", "&gt;")
                    content = content.replace("\n\n", '\n')
                    content = content.replace("\n", '<br style="line-height: 0.5rem;">\n')

                    details_logs = self._htree.element("details")
                    summary_logs = HTMLNode(details_logs.identifier, None, "summary",
                                            value=get_msg(MSG_EXPAND_FOR_CONTENT).format(entry=entry, content_len=len(content)))
                    details_logs.append_child(summary_logs)
                    div_logs = HTMLNode(
                        details_logs.identifier, None, "div",
                        attributes={"class": "font-mono", "style": "font-size: 80%;"}, value=content)
                    details_logs.append_child(div_logs)

    # -----------------------------------------------------------------------

    def pages_frequencies(self):
        """Add nodes to see the access frequency of pages.
        
        """
        pages, monthes = self._get_pages()
        max_value = 0

        h2 = self._htree.element("h2")
        h2.set_value(get_msg(MSG_TITLE_SEE_FREQ))

        # Add a table with overall counts
        h3 = self._htree.element("h3")
        h3.set_value(get_msg(MSG_FREQ_OVERALL))

        table = self._htree.element("table")
        table.add_attribute("role", "grid")
        table_content = list()
        table_content.append("<thead><tr>"
                             f"<th>{get_msg(MSG_PAGE_SENT)}</th>"
                             f"<th>{get_msg(MSG_OCC)}</th>"
                             "</tr></thead>")
        for page_name in pages:
            count = 0
            for m in pages[page_name]:
                value = pages[page_name][m]
                count += value
                if value > max_value:
                    max_value = pages[page_name][m]
            table_content.append(f"<tr><td>{page_name}</td><td>{count}</td></tr>")
        table.set_value("\n".join(table_content))

        # Add an histogram for each page/month

        h3 = self._htree.element("h3")
        h3.set_value(get_msg(MSG_FREQ_DETAILS))

        for page_name in pages:
            color = hex_code_colors()
            t = self._htree.element("h4")
            t.set_value(page_name)
            t.set_attribute("style", f"color: {color};")
            div = self._htree.element("div")
            svg = self._generate_svg(monthes, pages[page_name], color, max_value)
            div.set_value(svg)

    # -----------------------------------------------------------------------

    def applied_filters(self):
        """Fill-in the list of log contents and add notes to see the contents.

        """
        found, not_found = self._get_filters()

        h2_logs = self._htree.element("h2")
        h2_logs.set_value(get_msg(MSG_TITLE_SEE_FILTERS))

        h3_logs = self._htree.element("h3")
        h3_logs.set_value(get_msg(MSG_FILTERS_INVALID) + f" ({len(not_found)})")

        t = self._htree.element("table")
        for some_filter in not_found:
            tr = HTMLNode(t.identifier, None, "tr")
            tr.set_value(self._add_filter_into_tr(some_filter))
            t.append_child(tr)

        h3_logs = self._htree.element("h3")
        h3_logs.set_value(get_msg(MSG_FILTERS_VALID) + f" ({len(found)})")

        t = self._htree.element("table")
        for some_filter in found:
            tr = HTMLNode(t.identifier, None, "tr")
            tr.set_value(self._add_filter_into_tr(some_filter))
            t.append_child(tr)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def _get_pages(self):
        pages = dict()  # dict[page_name][month]
        monthes = list()
        for content in self.__logs:
            for line in content.split("\n"):
                if "Requested page name: " in line:
                    tab = line.split(" ")
                    page_name = tab[-1]
                    full_date = tab[0].split("-")
                    try:
                        month = float(full_date[0] + "." + full_date[1])
                        if page_name.endswith(".html") is True:
                            if page_name not in pages:
                                pages[page_name] = dict()
                            if month not in pages[page_name]:
                                pages[page_name][month] = 0
                            pages[page_name][month] += 1
                            if month not in monthes:
                                monthes.append(month)
                    except Exception as e:
                        logging.error(" ... " + str(e))
        return pages, monthes

    # -----------------------------------------------------------------------

    def _generate_svg(self, monthes, page, color, max_value):
        """Return an SVG image with an histogram."""
        w = 800
        h = 400
        margin = 20  # allows to write axes labels and legend
        step = (w - margin) / (len(monthes) + 1)
        bar_width = w // ((len(monthes)+1)*2)
        max_h = h - (margin*2)  # the height for the max_value

        svg = list()
        svg.append(f'<svg width="{w}" height="{h}">')

        # The y-axes is a vertical line
        svg.append(f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{h-margin}" '
                   f'stroke="black" stroke-width="2" />')
        # The x-axes is a horizontal line
        svg.append(f'<line x1="{margin}" y1="{h-margin}" x2="{w}" y2="{h-margin}" '
                   f'stroke="black" stroke-width="2" />')

        # The x-axes labels are the months
        for i, m in enumerate(sorted(monthes)):
            svg.append(f'<text x="{(step*(i+1))}" y="{h-4}" text-anchor="middle">{m}</text>')

        # data bars
        for i, m in enumerate(sorted(monthes)):
            if m in page:
                value = page[m]
            else:
                value = 0
            y = h - margin - (value*max_h/max_value)
            svg.append(f'<rect x="{(step*(i+1))-(bar_width//2)}" y="{y}" '
                       f'width="{bar_width}" height="{h - margin - y}" fill="{color}" '
                       f'class="getData" data-legend="{m}" />')

        # legend
        for i, m in enumerate(sorted(monthes)):
            if m in page:
                value = page[m]
            else:
                value = 0
            y = h - margin - (value*max_h/max_value)
            svg.append(f'<text x="{(step*(i+1))}" y="{y-4}" '
                       f'text-anchor="middle" class="legend" id="{m}">{value}</text>')
        svg.append(f'</svg>')
        return "\n".join(svg)

    # -----------------------------------------------------------------------

    def _get_filters(self):
        found = list()
        not_found = list()
        for content in self.__logs:
            all_lines = content.split("\n")
            i = 0
            while i < len(all_lines):
                if "Apply filters: " in all_lines[i]:
                    filters = list()
                    filters_date = None
                    while "Found " not in all_lines[i] and " documents" not in all_lines[i]:
                        if "Merging " not in all_lines[i]:
                            if filters_date is None:
                                _tmp = all_lines[i].split(" ")
                                filters_date = _tmp[0] if len(_tmp) > 0 else None
                            if "[" in all_lines[i] and "]" in all_lines[i]:  # should always be True
                                s = all_lines[i].index("[")
                                e = all_lines[i].rindex("]")
                                applied_filter = self._applied_filter_to_list(all_lines[i][s+1:e])
                                filters.append(applied_filter)
                        i += 1
                    if filters_date is not None:
                        if ' 0 ' in all_lines[i]:
                            not_found.append((filters_date, filters))
                        else:
                            found.append((filters_date, filters))
                i += 1
        return found, not_found

    # -----------------------------------------------------------------------

    @staticmethod
    def _add_filter_into_tr(some_filter: tuple):
        """Return the content of a table row filled with the given filter."""
        content = list()
        # Column 1: date
        content.append('<td>')
        content.append(some_filter[0])
        content.append("</td>")
        # Column 2: filters
        content.append('<td><ul>')
        for f in some_filter[1]:
            if isinstance(f[0], tuple) is True:
                for ff in f:
                    content.append("<li>")
                    content.append(" ".join(str(c) for c in ff))
                    content.append("</li>")
            else:
                content.append("<li>")
                content.append(" ".join(str(c) for c in f))
                content.append("</li>")
        content.append("</ul></td>")
        return "\n".join(content)

    # -----------------------------------------------------------------------

    @staticmethod
    def _applied_filter_to_list(f):
        try:
            return ast.literal_eval(f)
        except (SyntaxError, ValueError):
            return None
