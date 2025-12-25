"""
:filename: whakerkit.documents.docs_filters.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filter for documents.

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

from ..documents.document_utils import DocumentUtils
from ..filters.basefilters import BaseFilters
from ..filters.strcompare import StringComparator
from ..filters.datecompare import DatetimeComparator
from ..filters.filteredset import FilteredSet

# ---------------------------------------------------------------------------


class DocumentsFilters(BaseFilters):
    """Filter system for document files.

    :example:
    >>> # Create a filter:
    >>> f = DocumentsFilters(FilesList)

    Then, apply a filter with some pattern like in the following examples.
    The result can be combined with operators & and |, like for any other
    'set' in Python, 'an unordered collection of distinct hashable objects'.

    Four different filters can be applied:
    1. author (str)
    2. date (datetime.date or datetime.datetime)
    3. filename (str)
    4. filetype (str)

    :example:
    >>> # folder name indicates author is "toto"
    >>> f.author(exact='toto')
    >>> # folder date indicates date is between 2022 and 2024
    >>> f.date(gt=(2024,3,12)) & f.date(lt=(2024,5,1))
    >>> # It's equivalent to write - the latter is faster:
    >>> f.date(gt=(2024,3,12), lt=(2024,5,1), logic_bool="and")
    >>> # author is toto and date is after or equal 2024
    >>> f.author(exact='toto') & f.date(ge=(2024,1,1)) & f.filetype(exact='pptx')

    The classical "and" and "or" logical boolean predicates are accepted;
    "and" is the default one. It defines whether all the functions must
    be True ("and") or any of them ("or").

    """

    def __init__(self, obj):
        """Create a DocumentsFilters instance.

        The given object must have the 4 following attributes:
        1. author (str)
        2. date (datetime.date or datetime.datetime)
        3. filename (str)
        4. filetype (str)
        5. description (str)

        :param obj: (any) The object to be filtered.
        :raises: TypeError: Invalid given object

        """
        if isinstance(obj, list) is False:
            raise TypeError("Expected a list of files. Got {} instead.".format(type(obj)))
        super(DocumentsFilters, self).__init__(obj)
        if len(obj) > 0:
            try:
                # Check if object is iterable
                for item in self._obj:
                    # Check if object items have all required attributes -- either member or property
                    item.author
                    item.date
                    item.filename
                    item.filetype
                    item.description
                    break
            except AttributeError as e:
                raise TypeError("Invalid given object: {}".format(e))

    # -----------------------------------------------------------------------

    def author(self, **kwargs) -> FilteredSet:
        """Apply functions on all items of the object to filter on the author.

        Each argument is made of a function name and its expected value.
        Each function can be prefixed with 'not_', like in the next example.

        :Example:
        >>> f = DocumentsFilters(list(FilesObject))
        >>> f.author(startswith="pa", not_endswith='a', logic_bool="and")
        >>> f.author(startswith="pa") & f.author(not_endswith='a')
        >>> f.author(startswith="pa") | f.author(startswith="ta")

        :param kwargs: logic_bool/any StringComparator() method.
        :return: (FilterSet) Filter set.

        """
        comparator = StringComparator()

        # extract the information from the arguments
        BaseFilters.test_args(comparator, **kwargs)
        logic_bool = BaseFilters.fix_logic_bool(**kwargs)
        string_functions = BaseFilters.fix_functions(comparator, **kwargs)

        # search for the files matching the given filters
        data = FilteredSet()
        for item in self._obj:
            is_matching = StringComparator.match(item.author, string_functions, logic_bool)
            if is_matching is True:
                # Store both the item of the object and the filter which makes it true
                data.append(item)

        return data

    # -----------------------------------------------------------------------

    def filename(self, **kwargs) -> FilteredSet:
        """Apply functions on all items of the object to filter on the filename.

        Each argument is made of a function name and its expected value.
        Each function can be prefixed with 'not_', like in the next example.

        :Example:
        >>> f = DocumentsFilters(list(FilesObject))
        >>> f.filename(startswith="pa", not_endswith='a', logic_bool="and")
        >>> f.filename(startswith="pa") & f.author(not_endswith='a')
        >>> f.filename(startswith="pa") | f.author(startswith="ta")

        :param kwargs: logic_bool/any StringComparator() method.
        :return: (FilterSet) Filter set.

        """
        comparator = StringComparator()

        # extract the information from the arguments
        BaseFilters.test_args(comparator, **kwargs)
        logic_bool = BaseFilters.fix_logic_bool(**kwargs)
        string_functions = BaseFilters.fix_functions(comparator, **kwargs)

        # search for the files matching the given filters
        data = FilteredSet()
        for item in self._obj:
            is_matching = StringComparator.match(item.filename, string_functions, logic_bool)
            if is_matching is True:
                data.append(item)

        return data

    # -----------------------------------------------------------------------

    def filetype(self, **kwargs) -> FilteredSet:
        """Apply functions on all items of the object to filter on the filetype.

        Each argument is made of a function name and its expected value.
        Each function can be prefixed with 'not_', like in the next example.

        :Example:
        >>> f = DocumentsFilters(list(FilesObject))
        >>> f.filetype(startswith="t", not_endswith='t', logic_bool="and")
        >>> f.filetype(startswith="ppt") & f.filetype(not_endswith='x')
        >>> f.filetype(startswith="ppt") | f.filetype(startswith="doc")

        :param kwargs: logic_bool/any StringComparator() method.
        :return: (FilterSet) Filter set.

        """
        comparator = StringComparator()

        # extract the information from the arguments
        BaseFilters.test_args(comparator, **kwargs)
        logic_bool = BaseFilters.fix_logic_bool(**kwargs)
        string_functions = BaseFilters.fix_functions(comparator, **kwargs)

        # search for the files matching the given filters
        data = FilteredSet()
        for item in self._obj:
            is_matching = StringComparator.match(item.filetype, string_functions, logic_bool)
            if is_matching is True:
                data.append(item)

        return data

    # -----------------------------------------------------------------------

    def date(self, **kwargs) -> FilteredSet:
        """Apply functions on all items of the object.

        Each argument is made of a function name and its expected value.
        Each function can be prefixed with 'not_', like in the next example.

        :param kwargs: logic_bool/any StringComparator() method.
        :return: (FilterSet) Filter set.

        """
        comparator = DatetimeComparator()

        # extract the information from the arguments
        BaseFilters.test_args(comparator, **kwargs)
        logic_bool = BaseFilters.fix_logic_bool(**kwargs)
        date_functions = BaseFilters.fix_functions(comparator, **kwargs)

        # search for the files matching the given filters
        data = FilteredSet()
        for item in self._obj:
            is_matching = DatetimeComparator.match(item.date, date_functions, logic_bool)
            if is_matching is True:
                data.append(item)

        return data

    # -----------------------------------------------------------------------

    def description(self, **kwargs) -> FilteredSet:
        """Apply functions on all items of the object to filter on the description.

        Each argument is made of a function name and its expected value.
        Each function can be prefixed with 'not_', like in the next example.

        :Example:
        >>> f = DocumentsFilters(list(FilesObject))
        >>> f.description(startswith="pa", not_endswith='a', logic_bool="and")
        >>> f.description(startswith="pa") & f.description(not_endswith='a')
        >>> f.description(startswith="pa") | f.description(startswith="ta")

        :param kwargs: logic_bool/any StringComparator() method.
        :return: (FilterSet) Filter set.

        """
        comparator = StringComparator()

        # extract the information from the arguments
        BaseFilters.test_args(comparator, **kwargs)
        logic_bool = BaseFilters.fix_logic_bool(**kwargs)
        string_functions = BaseFilters.fix_functions(comparator, **kwargs)

        # search for the files matching the given filters
        data = FilteredSet()
        for item in self._obj:
            is_matching = StringComparator.match(item.description, string_functions, logic_bool)
            if is_matching is True:
                data.append(item)

        return data

    # -----------------------------------------------------------------------

    @staticmethod
    def cast_data(filter_fct: str, entry: str):
        """Return the entry into the appropriate type.

        :param filter_fct: (str) Name of the filter (filename, date, ...)
        :param entry: (any) The entry to cast
        :return: typed entry
        :raises: KeyError: if filter_fct is unknown

        """
        if filter_fct == "date":
            return DocumentUtils.str_to_date(entry)

        elif filter_fct == "filetype":
            return DocumentUtils.format_filetype(entry)

        elif filter_fct == "filename":
            return DocumentUtils.format_filename(entry)

        elif filter_fct == "author":
            return DocumentUtils.format_author(entry)

        elif filter_fct == "description":
            return DocumentUtils.format_description(entry)

        else:
            raise KeyError("Unknown filter function {:s}.".format(filter_fct))

    # -----------------------------------------------------------------------

    @staticmethod
    def merge_data(filtered_sets: list, match_all: bool = False) -> FilteredSet:
        """Return merged filtered data sets.

        If match_all is False (the default), the operator '|' is applied
        between the given filters: it's the *union* of all filtered sets.
        If match_all is True, the operator '&' is applied between the given
        filters: it's the *intersection* of all filtered sets.

        :example:
        >>> fs1 = FilteredSet()
        >>> fs2 = FilteredSet()
        >>> fs3 = FilteredSet()
        >>> fs1.append("data1")
        >>> fs2.append("data2")
        >>> fs2.append("data1")
        >>> fs3.append("data3")
        >>> fs3.append("data1")
        >>> DocumentsFilters.merge_data([fs1, fs2, fs3], match_all=False)
        ['data1', 'data2', 'data3']
        >>> DocumentsFilters.merge_data([fs1, fs2, fs3], match_all=True)
        ['data1']

        :param filtered_sets: (list) List of filtered data sets.
        :param match_all: (bool) If True, returned files must match all the given filters
        :raises: TypeError: invalid parameter
        :return: (FilteredSet)

        """
        # Empty list of filtered sets or invalid type
        if len(filtered_sets) == 0:
            return FilteredSet()
        for i in range(len(filtered_sets)):
            if isinstance(filtered_sets[i], FilteredSet) is False:
                raise TypeError("Expected a FilteredSet. Got {:s} instead"
                                "".format(str(type(filtered_sets[i]))))
        # No match to perform if only one set
        if len(filtered_sets) == 1:
            return filtered_sets[0]

        if isinstance(match_all, bool) is False:
            raise TypeError("Expected a boolean for the match function {:s}. Got '{:s}' instead."
                            "".format(str(match_all), str(type(match_all))))

        # Apply a logical 'AND' or 'OR' on the filtered sets
        files_set = filtered_sets[0]
        if match_all is True:
            # Apply "&" operator between the filtered sets
            for i in range(1, len(filtered_sets)):
                files_set = files_set & filtered_sets[i]
                if len(files_set) == 0:
                    break
        else:
            # Apply "|" operator between the filtered sets
            for i in range(1, len(filtered_sets)):
                files_set = files_set | filtered_sets[i]

        return files_set
