"""
:filename: whakerkit.filters.basefilters.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Base class for any filter system.

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

from .basecompare import BaseComparator

# ---------------------------------------------------------------------------


class BaseFilters:
    """Base class for any filter system.

    Provides a foundational framework for filtering objects using various
    comparison methods. It ensures that the filtering criteria are valid and
    processes logical operations on these criteria.

    :example:
    >>> obj = SomeObject()
    >>> comparator = BaseComparator()
    >>> comparator._methods['exact'] = lambda x, y: x == y
    >>> kwargs = {'exact': "10"}
    >>> # Here it is:
    >>> base_filters = BaseFilters(obj)
    >>> BaseFilters.test_args(comparator, **kwargs)
    >>> logic_bool = BaseFilters.fix_logic_bool(**kwargs)
    >>> functions = BaseFilters.fix_functions(comparator, **kwargs)
    >>> # search for the object items matching the given filter
    >>> for item in obj:
    >>>    if comparator.match(item, functions, logic_bool):
    >>>        yield item

    """

    def __init__(self, obj: object):
        """Create a BaseFilters instance.

        :param obj: (object) Any type of object to be filtered.

        """
        self._obj = obj

    # -----------------------------------------------------------------------

    @staticmethod
    def test_args(comparator: BaseComparator, **kwargs) -> None:
        """Raise an exception if any of the kwargs is not correct.

        :param comparator: (BaseComparator)
        :raises: KeyError: Invalid argument for the given comparator.

        """
        names = ["logic_bool"] + comparator.get_function_names()
        for func_name, value in kwargs.items():
            if func_name.startswith("not_"):
                func_name = func_name[4:]

            if func_name not in names:
                raise KeyError(f"Invalid kwargs function name {func_name}")

    # -----------------------------------------------------------------------

    @staticmethod
    def fix_logic_bool(**kwargs) -> str:
        """Return the value of a logic boolean predicate.

        Expect at least the "logic_bool" argument.

        :raises: ValueError: Invalid logic bool value.
        :return: (str) "and" or "or". By default, the logical "and" is returned.

        """
        for func_name, value in kwargs.items():
            if func_name == "logic_bool":
                if value not in ['and', 'or']:
                    raise ValueError("Invalid logic bool {}".format(func_name))
                return value
        return "and"

    # -----------------------------------------------------------------------

    @staticmethod
    def fix_functions(comparator: BaseComparator, **kwargs) -> list:
        """Parse the args to get the list of (function,value,complement).

        The complement is a boolean which is True if the function is prefixed
        with "not_", meaning that the expected result is the opposite of the
        function.

        :param comparator: (BaseComparator)
        :return: (list) List of tuples with (function, value, complement)

        """
        f_functions = list()
        for func_name, value in kwargs.items():

            logical_not = False
            if func_name.startswith("not_"):
                logical_not = True
                func_name = func_name[4:]

            if func_name in comparator.get_function_names():
                f_functions.append((comparator.get(func_name), value, logical_not))

        return f_functions
