"""
:filename: whakerkit.nodes.filter_node.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: A node to filter documents.

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

from whakerpy.htmlmaker import EmptyNode
from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg
from ..config import TypesDealer

from .utils import create_action_button

# ---------------------------------------------------------------------------


MSG_TITLE_FILTERS = "Filters:"
MSG_DO_FILTER = "Filter documents"
MSG_CLEAR_FILTER = "Clear filters"
MSG_DOCUMENTS = "The document"
MSG_CONDITIONS_ALL = "meets all of the following criteria"
MSG_CONDITIONS_OR = "meets at least one of the following criteria"
MSG_FILETYPE_IS = "File type is"
MSG_AUTHOR_IS = "Author is"
MSG_SELECTION_AMONG = "among:"
MSG_DATE_AMONG = "The deposit date is between"
MSG_NAME_OR_DESCR = "The name or description"
MSG_STARTYEAR = "start year"
MSG_ENDYEAR = "end year"
MSG_THIS_THAT = "this OR/AND that"
MSG_OR = "OR"
MSG_AND = "AND"
MSG_ACONTAINS = "contains"
MSG_NOT_ACONTAINS = "does not contain"
MSG_CONTAINS = "contains (with diacritics)"
MSG_NOT_CONTAINS = "does not contain (with diacritics)"
MSG_STARTSWITH = "starts with"
MSG_ENDSWITH = "ends with"

# ---------------------------------------------------------------------------


class WhakerKitFilterNode(HTMLNode):
    """Node with a multi-criteria filtering system to access documents.

    """

    def __init__(self, parent, filetypes: list, authors: list):
        """Create the filter node.

        The ID of this node can be used in a JS to clear/reset the filters to
        their default values.

        :param parent: (HTMLNode) The parent node identifier
        :param filetypes: (list) A list of the file types to filter
        :param authors: (list) A list of the authors to filter

        """
        super(WhakerKitFilterNode, self).__init__(parent, "filters_details", "details",
                                                  attributes={"class": "width-full",
                                                     "open": None,
                                                     "id": "filters_details"})

        summary = HTMLNode(self.identifier, None, "summary", value=get_msg(MSG_TITLE_FILTERS))
        self.append_child(summary)

        main = HTMLNode(self.identifier, None, "main")
        self.append_child(main)

        # Add table to apply any or all criteria
        # self.__append_table_for_any_or_all_conditions(main)

        # Authors filter
        self.__append_details(
            main, "author", get_msg(MSG_AUTHOR_IS) + " " + get_msg(MSG_SELECTION_AMONG),
            "toggleSelectorAuthor.toggleSelection(event)", authors)

        # File type filter
        self.__append_details(
            main, "filetype", get_msg(MSG_FILETYPE_IS) + " " + get_msg(MSG_SELECTION_AMONG),
            "toggleSelectorFiletype.toggleSelection(event)", filetypes)

        # Filename and description filter
        # -------------------------------

        table_filename = HTMLNode(
            main.identifier, None, "table",
            attributes={"role": "presentation"})
        main.append_child(table_filename)

        tbody_filename = HTMLNode(table_filename.identifier, None, "tbody")
        table_filename.append_child(tbody_filename)

        tr_description = HTMLNode(tbody_filename.identifier, None, "tr")
        tbody_filename.append_child(tr_description)

        # 1st column: label
        td_description_label = HTMLNode(tr_description.identifier, None, "td",
                                        value=get_msg(MSG_NAME_OR_DESCR))
        tr_description.append_child(td_description_label)

        # 2nd column: condition
        td_description_select = HTMLNode(tr_description.identifier, None, "td")
        tr_description.append_child(td_description_select)

        select_description = HTMLNode(
            td_description_select.identifier, None, "select",
            attributes={"aria-label": get_msg(MSG_CONTAINS),
                        "id": "description_condition", "name": "description_condition",
                        "style": "width: 100%;"})
        td_description_select.append_child(select_description)

        options_description = [
            ("acontains", get_msg(MSG_ACONTAINS)),
            ("not_acontains", get_msg(MSG_NOT_ACONTAINS)),
            ("contains", get_msg(MSG_CONTAINS)),
            ("not_contains", get_msg(MSG_NOT_CONTAINS)),
            ("astartswith", get_msg(MSG_STARTSWITH)),
            ("aendswith", get_msg(MSG_ENDSWITH))
        ]
        for i, option in enumerate(options_description):
            opt = HTMLNode(select_description.identifier, None, "option",
                           attributes={"value": option[0]},
                           value=option[1])
            if i == 0:
                opt.add_attribute("selected", "selected")
            select_description.append_child(opt)

        # 3rd column: user text input
        td_description_input = HTMLNode(tr_description.identifier, None, "td", attributes={"class": "width_40"},)
        tr_description.append_child(td_description_input)

        label_description = HTMLNode(td_description_input.identifier, None, "label", attributes={
            "for": "description_input", "id": "description_label",
            "aria-label": "description du fichier"})
        td_description_input.append_child(label_description)

        input_description = HTMLNode(label_description.identifier, None, "input", attributes={
            "class": "filter-choice", "id": "description_input", "type": "text",
            "aria-labelledby": "description_label", "placeholder": get_msg(MSG_THIS_THAT),
            "style": "width: 100%;"
        })
        label_description.append_child(input_description)

        # 4th column: toggle switch
        td_switch_input = HTMLNode(tr_description.identifier, None, "td")
        tr_description.append_child(td_switch_input)

        label = HTMLNode(td_switch_input.identifier, None, "label",
                         attributes={"class": "switch", "id": "switch_description_label"})
        td_switch_input.append_child(label)
        check = HTMLNode(label.identifier, None, "input", attributes={"type": "checkbox", "checked": "checked"})
        label.append_child(check)
        span = HTMLNode(label.identifier, None, "span", attributes={"class": "switch-slider"})
        label.append_child(span)
        or_span = HTMLNode(span.identifier, None, "span", attributes={"class": "switch-off-text"}, value=get_msg(MSG_OR))
        and_span = HTMLNode(span.identifier, None, "span", attributes={"class": "switch-on-text"}, value=get_msg(MSG_AND))
        span.append_child(and_span)
        span.append_child(or_span)

        # Date
        # ----
        tr_date = HTMLNode(tbody_filename.identifier, None, "tr")
        tbody_filename.append_child(tr_date)

        td_date_label = HTMLNode(tr_date.identifier, None, "td", value=get_msg(MSG_DATE_AMONG))
        tr_date.append_child(td_date_label)

        td_date_min = HTMLNode(tr_date.identifier, None, "td")
        tr_date.append_child(td_date_min)

        input_date_min = HTMLNode(td_date_min.identifier, None, "input", attributes={
            "class": "flex-item filter-choice", "id": "date_min_input", "type": "text",
            "aria-label": get_msg(MSG_STARTYEAR), "placeholder": "YYYY", "maxlength": "4",
            "aria-labelledby": "date_min_label", "style": "width: 6rem"})
        td_date_min.append_child(input_date_min)

        td_date_max = HTMLNode(tr_date.identifier, None, "td")
        tr_date.append_child(td_date_max)

        input_date_max = HTMLNode(td_date_max.identifier, None, "input", attributes={
            "class": "flex-item filter-choice", "id": "date_max_input", "type": "text",
            "aria-label": get_msg(MSG_ENDYEAR), "aria-labelledby": "date_min_label",
            "maxlength": "4", "placeholder": "YYYY", "style": "width: 6rem"})
        td_date_max.append_child(input_date_max)

        # empty 4th column
        td_switch_input = HTMLNode(tr_date.identifier, None, "td")
        tr_date.append_child(td_switch_input)

        # Action buttons: apply filters or clear fields
        self.__append_action_buttons(main)

    # -----------------------------------------------------------------------

    def __append_details(self, parent: HTMLNode, name: str, summary_span: str, onclick: str, elements: list):
        # Create the details element
        details = HTMLNode(parent.identifier, name + "_details", "details")
        details.add_attribute("id", name + "_details")
        parent.append_child(details)

        # Create and add the 'summary' element
        summary = HTMLNode(details.identifier, None, "summary")
        summary.add_attribute("class", "summary-choice")
        details.append_child(summary)
        # The summary is made of a text in a span element, and
        # an action button to toggle checkboxes
        span = HTMLNode(summary.identifier, None, "span", value=summary_span)
        summary.append_child(span)
        button = HTMLNode(summary.identifier, None, "button", attributes={
            "data-toggle": "",
            "class": "accordion-action",
            "onclick": onclick,
            "onkeydown": onclick
        })
        summary.append_child(button)
        img = EmptyNode(button.identifier, None, "img", attributes={"src": "", "alt": ""})
        button.append_child(img)

        # Create and add the 'main' element
        main = HTMLNode(details.identifier, None, "main")
        details.append_child(main)
        # The main is made of a list of checkboxes
        ul = HTMLNode(main.identifier, None, "ul")
        main.append_child(ul)
        for elt in elements:
            elt_id = TypesDealer.remove_diacritics_and_non_ascii(elt)
            li = HTMLNode(ul.identifier, None, "li", attributes={"class": "check-item"})
            ul.append_child(li)
            checkbox = EmptyNode(li.identifier, None, "input", attributes={
                "id": f"{elt_id}_input",
                "data-toggle": name,
                "type": "checkbox",
                "aria-labelledby": f"{elt_id}_label",
                "checked": "checked",
            })
            li.append_child(checkbox)
            label = HTMLNode(li.identifier, None, "label",
                             attributes={"for": f"{elt_id}_input", "id": f"{elt_id}_label",
                                         "aria-label": elt_id}, value=elt)
            li.append_child(label)
        return details

    # -----------------------------------------------------------------------

    def __append_action_buttons(self, parent: HTMLNode):
        """Append the centered action buttons.

        """
        # Organize action buttons in a menu
        actions = HTMLNode(parent.identifier, None, "section")
        actions.add_attribute("class", "flex-panel")
        parent.append_child(actions)

        btn = create_action_button(
                actions.identifier, "docManager.filterDocuments();",
                get_msg(MSG_DO_FILTER), whakerkit.sg.path + "statics/icons/filter.png")
        actions.append_child(btn)

        btn = create_action_button(
                actions.identifier, "docManager.resetFilters();",
                get_msg(MSG_CLEAR_FILTER), whakerkit.sg.path + "statics/icons/clear.png")
        actions.append_child(btn)
