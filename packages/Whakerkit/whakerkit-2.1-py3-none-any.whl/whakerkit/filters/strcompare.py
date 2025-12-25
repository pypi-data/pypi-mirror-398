"""
:filename: whakerkit.filters.strcompare.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Comparator system for strings.

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

import re

from ..config import TypesDealer

from .basecompare import BaseComparator

# ---------------------------------------------------------------------------


class StringComparator(BaseComparator):
    """Comparison methods for strings.

    Extend BaseComparator() to provide various string comparison methods.
    It includes methods for exact matches, case-insensitive matches,
    diacritics-insensitive matches, and pattern matching using regular
    expressions.
    The class ensures that the inputs are strings and raises appropriate
    errors for invalid inputs.

    :example:
    >>> sc = StringComparator()
    >>> sc.exact("abc", "abc")
    True
    >>> sc.get('exact')("abc", "abc")
    True
    >>> sc.istartswith("hello", "HE")
    True
    >>> sc.regexp("hello123", r"\\d+")
    True

    """

    def __init__(self):
        """Create a StringComparator instance.

        """
        super().__init__()

        # Methods for comparison on strings
        self._methods['exact'] = StringComparator.exact
        self._methods['iexact'] = StringComparator.iexact
        self._methods['aexact'] = StringComparator.aexact
        self._methods['startswith'] = StringComparator.startswith
        self._methods['istartswith'] = StringComparator.istartswith
        self._methods['astartswith'] = StringComparator.astartswith
        self._methods['endswith'] = StringComparator.endswith
        self._methods['iendswith'] = StringComparator.iendswith
        self._methods['aendswith'] = StringComparator.aendswith
        self._methods['contains'] = StringComparator.contains
        self._methods['icontains'] = StringComparator.icontains
        self._methods['acontains'] = StringComparator.acontains
        self._methods['regexp'] = StringComparator.regexp

    # -----------------------------------------------------------------------

    @staticmethod
    def _check_string(s: str) -> None:
        """Raise TypeError if the given parameter is not a string.

        :param s: (str) A string to be checked.
        :raises: TypeError: If the given parameter is not a string.

        """
        if isinstance(s, str) is False:
            raise TypeError(f"Expected a string. Got {str(type(s))} instead.")

    # -----------------------------------------------------------------------

    @staticmethod
    def exact(s1: str, s2: str) -> bool:
        """Test if two strings strictly contain the same characters.

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1 == s2

    # -----------------------------------------------------------------------

    @staticmethod
    def iexact(s1: str, s2: str) -> bool:
        """Test if two strings contain the same characters (case-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1.lower() == s2.lower()

    # -----------------------------------------------------------------------

    @staticmethod
    def aexact(s1: str, s2: str) -> bool:
        """Test if two strings contain the same characters (case-insensitive, diacritics-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        # Remove diacritics and non-ascii characters
        s1 = s1.lower()
        s2 = s2.lower()
        return TypesDealer.remove_diacritics_and_non_ascii(s1) == TypesDealer.remove_diacritics_and_non_ascii(s2)

    # -----------------------------------------------------------------------

    @staticmethod
    def startswith(s1: str, s2: str) -> bool:
        """Test if the first string starts with the second string.

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1.startswith(s2)

    # -----------------------------------------------------------------------

    @staticmethod
    def istartswith(s1: str, s2: str) -> bool:
        """Test if the first string starts with the second string (case-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1.lower().startswith(s2.lower())

    # -----------------------------------------------------------------------

    @staticmethod
    def astartswith(s1: str, s2: str) -> bool:
        """Test if the first string starts with the second string (case-insensitive, diacritics-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        # Remove diacritics and non-ascii characters
        s1 = s1.lower()
        s2 = s2.lower()
        s1 = TypesDealer.remove_diacritics_and_non_ascii(s1)
        s2 = TypesDealer.remove_diacritics_and_non_ascii(s2)
        return s1.startswith(s2)

    # -----------------------------------------------------------------------

    @staticmethod
    def endswith(s1: str, s2: str) -> bool:
        """Test if the first string ends with the second string.

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1.endswith(s2)

    # -----------------------------------------------------------------------

    @staticmethod
    def iendswith(s1: str, s2: str) -> bool:
        """Test if the first string ends with the second string (case-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s1.lower().endswith(s2.lower())

    # -----------------------------------------------------------------------

    @staticmethod
    def aendswith(s1: str, s2: str) -> bool:
        """Test if the first string ends with the second string (case-insensitive, diacritics-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        # Remove diacritics and non-ascii characters
        s1 = s1.lower()
        s2 = s2.lower()
        s1 = TypesDealer.remove_diacritics_and_non_ascii(s1)
        s2 = TypesDealer.remove_diacritics_and_non_ascii(s2)
        return s1.endswith(s2)

    # -----------------------------------------------------------------------

    @staticmethod
    def contains(s1: str, s2: str) -> bool:
        """Test if the first string contains the second string.

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s2 in s1

    # -----------------------------------------------------------------------

    @staticmethod
    def icontains(s1: str, s2: str) -> bool:
        """Test if the first string contains the second string (case-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        return s2.lower() in s1.lower()

    # -----------------------------------------------------------------------

    @staticmethod
    def acontains(s1: str, s2: str) -> bool:
        """Test if the first string contains the second string (case-insensitive and diacritics-insensitive).

        :param s1: (str) String to compare.
        :param s2: (str) String to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s1)
        StringComparator._check_string(s2)
        # Remove diacritics and non-ascii characters
        s1 = s1.lower()
        s2 = s2.lower()
        return TypesDealer.remove_diacritics_and_non_ascii(s2) in TypesDealer.remove_diacritics_and_non_ascii(s1)

    # -----------------------------------------------------------------------

    @staticmethod
    def regexp(s: str, pattern: str) -> bool:
        """Test if the first string matches the second string.

        :param s: (str) String.
        :param pattern: (str) Pattern to match in string.
        :return: (bool)
        :raises: TypeError: invalid given parameter.

        """
        StringComparator._check_string(s)
        StringComparator._check_string(pattern)
        return True if re.match(pattern, s) else False
