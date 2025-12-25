"""
:filename: whakerkit.filters.basecompare.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class for any comparator system.

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


class BaseComparator:
    """Base class for any comparator system.

    Serve as a foundational class for creating comparator systems. It manages
    a collection of comparison methods and provides functionality to retrieve
    and apply these methods to items.

    :example:
    >>> comparator = BaseComparator()
    >>> comparator._methods['exact'] = lambda x, y: x == y
    >>> comparator._methods['iexact'] = lambda x, y: x.lower() == y.lower()
    >>> # Retrieve a method
    >>> exact_method = comparator.get('exact')
    >>> print(exact_method('abc', 'abc'))
    True
    >>> # Get all method names
    >>> print(comparator.get_function_names())
    ['exact', 'iexact']
    >>> # Match item using methods
    >>> functions = [(comparator.get('exact'), 'abc', False)]
    >>> print(BaseComparator.match('abc', functions))
    True

    """

    def __init__(self):
        """Constructor of a BaseCompare.

        """
        # A dictionary that stores comparison methods, where the key is the
        # method name and the value is the method itself.
        self._methods = dict()

    # -----------------------------------------------------------------------

    def get(self, name: str):
        """Return the function of the given name.

        :param name: (str) The name of a method of this class

        """
        if name in self._methods:
            return self._methods[name]
        raise ValueError(f"Invalid function name {name}")

    # -----------------------------------------------------------------------

    def get_function_names(self) -> list:
        """Return the list of comparison method names.

        """
        return list(self._methods.keys())

    # -----------------------------------------------------------------------

    @staticmethod
    def match(item, functions: list, logic_bool: str = "and") -> bool:
        """Return True if the given item matches all or any of the functions.

        The functions parameter is a list of tuples to match against:
            - function: a function in python which takes 2 arguments: (item, value)
            - value: the expected value for the item
            - logical_not: boolean

        :param item: (any) Item to find a match
        :param functions: (list[tuples]) List of tuples(function, value, logical_not)
        :param logic_bool: (str) Apply a logical "and" or a logical "or" between the functions.
        :return: (bool)
        :raises: TypeError: Invalid functions parameter

        :Example:
        >>> # Search if a string is exactly matching "toto":
        >>> StringComparator.match("toto", [(exact, "toto", False)])
        True
        >>> StringComparator.match("TOTO", [(exact, "toto", False)])
        False
        >>> StringComparator.match("TOTO", [(iexact, "toto", False)])
        True
        >>> # Search if a string is starting with "p" or starting with "t":
        >>> StringComparator.match("my_string", [(startswith, "p", False), (startswith, "t", False)], logic_bool="or")
        False
        >>> # Search if a date is exactly (2024, 3, 4):
        >>> DatetimeComparator.match(datetime.date((2024, 3, 4)), [(equal, (2024, 3, 4), False)])
        True
        >>> # Search if a date is between two other ones:
        >>> DatetimeComparator.match(datetime.date((2024, 3, 4)),  [(gt, (2022, 1, 1), False), (lt, (2024, 12, 31), False)], logic_bool="and")
        True

        """
        if isinstance(functions, (list, tuple)) is False:
            raise TypeError("Invalid functions parameter {}.".format(functions))
        for f in functions:
            if len(f) != 3:
                raise TypeError("Invalid functions parameter {}.".format(functions))

        matches = list()
        for func, value, logical_not in functions:
            if logical_not is True:
                matches.append(not func(item, value))
            else:
                matches.append(func(item, value))

        if logic_bool == "and":
            return all(matches)
        else:
            return any(matches)
