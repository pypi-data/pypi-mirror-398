"""
:filename: whakerkit.filters.filterset.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Data class to store the result of any kind of filter.

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


class FilteredSet:
    """Manager for a list of filtered data.

    Manage a list of unique objects, similar to a set but with list-like
    append and remove methods. It supports union (|) and intersection (&)
    operations, deep copying, and equality checks.

    :example:
    >>> fs = FilteredSet()
    >>> fs.append("item1")
    >>> fs.append("item2")
    >>> print(len(fs))
    2
    >>> fs2 = FilteredSet()
    >>> fs2.append("item2")
    >>> fs2.append("item3")
    >>> union_fs = fs | fs2
    >>> print(len(union_fs))
    3
    >>> intersection_fs = fs & fs2
    >>> print(len(intersection_fs))
    1

    """

    def __init__(self):
        """Create a FilteredSet instance."""
        self._data_set = list()

    # -----------------------------------------------------------------------

    def append(self, data) -> bool:
        """Append a data in the data set, with the given value.

        :param data: (object)
        :return: (bool) Added or not

        """
        if data not in self._data_set:
            self._data_set.append(data)
            return True
        return False

    # -----------------------------------------------------------------------

    def remove(self, data) -> bool:
        """Remove the data of the data set.

        :param data: (object)
        :return: (bool) Removed or not

        """
        if data in self._data_set:
            # del self._data_set[data]
            self._data_set.remove(data)
            return True
        return False

    # -----------------------------------------------------------------------

    def copy(self):
        """Make a deep copy of self."""
        d = FilteredSet()
        for data in self._data_set:
            d.append(data)

        return d

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __iter__(self):
        for data in self._data_set:
            yield data

    # -----------------------------------------------------------------------

    def __len__(self):
        return len(self._data_set)

    # -----------------------------------------------------------------------

    def __contains__(self, data):
        return data in self._data_set

    # -----------------------------------------------------------------------

    def __eq__(self, other):
        """Check if data sets are equals, i.e. they share the same content."""
        # check len
        if len(self) != len(other):
            return False

        # check keys and values
        for key in self._data_set:
            if key not in other:
                return False

        return True

    # -----------------------------------------------------------------------

    def __str__(self):
        return str(self._data_set)

    # -----------------------------------------------------------------------
    # Operators
    # -----------------------------------------------------------------------

    def __or__(self, other):
        """Implements the '|' operator between 2 data sets.

        Usually, the '|' is a bitwise comparator. It is overridden, so it
        does the union operation between two filtered sets.

        :return: (FilteredSet) Union of two filtered sets.

        """
        # Copy self: all items of self will be in the union
        _d = self.copy()
        for data in other:
            # Append item of other if not already existing in _d
            _d.append(data)
        return _d

    # -----------------------------------------------------------------------

    def __and__(self, other):
        """Implements the '&' operator between 2 data sets.

        Usually, the '&' is a bitwise comparator. It is overridden, so it
        does the intersection operation between two filtered sets.

        :return: (FilteredSet) Intersection of two filtered sets.

        """
        _d = FilteredSet()
        for data in self._data_set:
            # Append only if data is both in self and other
            if data in other:
                _d.append(data)
        return _d
