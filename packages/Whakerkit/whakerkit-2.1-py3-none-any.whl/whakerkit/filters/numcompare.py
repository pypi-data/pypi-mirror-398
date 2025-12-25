"""
:filename: whakerkit.filters.numcompare.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Comparator system for numbers of type 'int' or 'float'.

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

from .basecompare import BaseComparator

# ---------------------------------------------------------------------------


class NumericComparator(BaseComparator):
    """Comparison methods for 'int' or 'float' objects.

    Extend the BaseComparator class to provide comparison methods specifically
    for numeric types (int and float). It includes methods to check equality,
    less than, less than or equal to, greater than, and greater than or equal
    to between two numeric values.
    The class ensures type consistency and raises appropriate errors for type
    mismatches.

    :Example:
    >>> tc = 4
    >>> tc.equal(4, 2*2)
    True
    >>> tc.get('ge')(8, 2*2*2)
    True

    """

    TYPES = (int, float)
    _ERROR_TYPES_MISMATCH = "Expected the same two types. Got {} and {} instead."
    
    def __init__(self):
        """Create a NumericComparator instance.

        """
        super().__init__()

        # The methods and their corresponding functions
        self._methods['equal'] = NumericComparator.equal
        self._methods['le'] = NumericComparator.le
        self._methods['lt'] = NumericComparator.lt
        self._methods['ge'] = NumericComparator.ge
        self._methods['gt'] = NumericComparator.gt

    # -----------------------------------------------------------------------

    @staticmethod
    def _check_numeric(entry: int | float) -> None:
        """Raise TypeError if not an int or float object.

        :param entry: (int|float) A date to be checked
        :raises: TypeError: d is not of the expected type

        """
        if isinstance(entry, NumericComparator.TYPES) is False:
            raise TypeError(f"Expected a numeric type. Got {str(type(entry))} instead.")

    # -----------------------------------------------------------------------

    @staticmethod
    def equal(a: int | float, b: int | float) -> bool:
        """Test if two numbers are equal to each other.

        :param a: (int|float) number to compare.
        :param b: (datetime) number to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        NumericComparator._check_numeric(a)
        NumericComparator._check_numeric(b)
        if type(a) is type(b):
            return a == b
        else:
            raise TypeError()

    # -----------------------------------------------------------------------

    @staticmethod
    def lt(a: int | float, b: int | float) -> bool:
        """Test if the first number is lower than the second number.

        :param a: (int|float) number to compare.
        :param b: (datetime) number to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        NumericComparator._check_numeric(a)
        NumericComparator._check_numeric(b)
        if type(a) is type(b):
            return a < b
        else:
            raise TypeError(NumericComparator._ERROR_TYPES_MISMATCH.format(str(type(a)), str(type(b))))

    # -----------------------------------------------------------------------

    @staticmethod
    def le(a: int | float, b: int | float) -> bool:
        """Test if the first number is before or equal to the second number.

        :param a: (int|float) number to compare.
        :param b: (datetime) number to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        NumericComparator._check_numeric(a)
        NumericComparator._check_numeric(b)
        if type(a) is type(b):
            return a <= b
        else:
            raise TypeError(NumericComparator._ERROR_TYPES_MISMATCH.format(str(type(a)), str(type(b))))

    # -----------------------------------------------------------------------

    @staticmethod
    def gt(a: int | float, b: int | float) -> bool:
        """Test if the first number is after the second number.

        :param a: (int|float) number to compare.
        :param b: (datetime) number to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        NumericComparator._check_numeric(a)
        NumericComparator._check_numeric(b)
        if type(a) is type(b):
            return a > b
        else:
            raise TypeError(NumericComparator._ERROR_TYPES_MISMATCH.format(str(type(a)), str(type(b))))

    # -----------------------------------------------------------------------

    @staticmethod
    def ge(a: int | float, b: int | float) -> bool:
        """Test if the first number is after or equal to the second number.

        :param a: (int|float) number to compare.
        :param b: (datetime) number to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        NumericComparator._check_numeric(a)
        NumericComparator._check_numeric(b)
        if type(a) is type(b):
            return a >= b
        else:
            raise TypeError(NumericComparator._ERROR_TYPES_MISMATCH.format(str(type(a)), str(type(b))))
