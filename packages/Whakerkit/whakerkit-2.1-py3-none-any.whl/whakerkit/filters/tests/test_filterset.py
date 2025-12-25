# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.filters.tests.test_filterset.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filters tests of the result of a filter.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io

    -------------------------------------------------------------------------


      ██╗    ██╗██╗  ██╗ █████╗ ██╗  ██╗███████╗██████╗ ██╗  ██╗██╗████████╗
      ██║    ██║██║  ██║██╔══██╗██║ ██╔╝██╔════╝██╔══██╗██║ ██╔╝██║╚══██╔══╝
      ██║ █╗ ██║███████║███████║█████╔╝ █████╗  ██████╔╝█████╔╝ ██║   ██║
      ██║███╗██║██╔══██║██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗██╔═██╗ ██║   ██║
      ╚███╔███╔╝██║  ██║██║  ██║██║  ██╗███████╗██║  ██║██║  ██╗██║   ██║
       ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝   ╚═╝

      a seamless toolkit for managing dynamic websites and shared documents.

    -------------------------------------------------------------------------

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

import unittest
from dataclasses import dataclass

from whakerkit.filters import FilteredSet

# ---------------------------------------------------------------------------


class TestFilterSet(unittest.TestCase):
    """Test filter result."""

    def setUp(self):
        self.s1 = "toto"
        self.s2 = "titi"
        self.s3 = "moi"

    # -----------------------------------------------------------------------

    def test_append(self):
        """Append an item and values."""

        d = FilteredSet()
        self.assertEqual(0, len(d))

        # append an entry
        d.append(self.s1)
        self.assertEqual(1, len(d))

        # do not append the same entry twice
        d.append(self.s1)
        self.assertEqual(1, len(d))

        # append a different one
        d.append(self.s2)
        self.assertEqual(2, len(d))

    # -----------------------------------------------------------------------

    def test_copy(self):
        """Test the copy of a data set."""

        d = FilteredSet()
        d.append(self.s1)
        d.append(self.s2)

        dc = d.copy()
        self.assertEqual(len(d), len(dc))

    # -----------------------------------------------------------------------

    def test_or(self):
        """Test logical "or" between two data sets."""

        d1 = FilteredSet()
        d2 = FilteredSet()

        d1.append(self.s1)
        d2.append(self.s1)

        res = d1 | d2
        self.assertEqual(1, len(res))

        d2.append(self.s1)
        res = d1 | d2
        self.assertEqual(1, len(res))

        d2.append(self.s2)
        res = d1 | d2
        self.assertEqual(2, len(res))

        d2.append(self.s2)
        res = d1 | d2
        self.assertEqual(2, len(res))

        d1.append(self.s3)
        res = d1 | d2
        self.assertEqual(3, len(res))

    # -----------------------------------------------------------------------

    def test_and(self):
        """Test logical "and" between two data sets."""

        d1 = FilteredSet()
        d2 = FilteredSet()
        d1.append(self.s1)
        d2.append(self.s1)

        result = d1 & d2
        self.assertEqual(1, len(result))

        # Nothing changed. s2 is only in d1.
        d1.append(self.s2)
        result = d1 & d2
        self.assertEqual(1, len(result))

        # OK. Add s2 in d2 too...
        d2.append(self.s2)
        result = d1 & d2
        self.assertEqual(2, len(result))

    # -----------------------------------------------------------------------

    def test_eq(self):
        """Test equality between two data sets."""

        d1 = FilteredSet()
        d2 = FilteredSet()
        d1.append(self.s1)
        d2.append(self.s1)
        self.assertEqual(d1, d2)
        self.assertEqual(d2, d1)

        d1.append(self.s2)
        d2.append(self.s3)
        self.assertNotEqual(d1, d2)

        d1.append(self.s3)
        d2.append(self.s2)
        self.assertEqual(d1, d2)

        # same content, sorted differently
        d1 = FilteredSet()
        d2 = FilteredSet()
        d1.append(self.s1)
        d1.append(self.s2)
        d2.append(self.s2)
        d2.append(self.s1)
        self.assertEqual(d1, d2)

    # -----------------------------------------------------------------------

    def test_eq_with_objects(self):
        """Test equality between two data sets."""
        @dataclass
        class Data:
            filename: str
            def __hash__(self):
                return hash(self.filename)

        data1 = Data('toto')
        data2 = Data('toto')

        d1 = FilteredSet()
        d2 = FilteredSet()
        d1.append(data1)
        d2.append(data1)
        self.assertEqual(d1, d2)
        self.assertEqual(d2, d1)

        # d1 == d2 because their data contents are equals.
        d1.append(data1)
        d2.append(data2)
        self.assertEqual(d1, d2)
        # however, d1 is not d2.
        self.assertFalse(d1 is d2)
