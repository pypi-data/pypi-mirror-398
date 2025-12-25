# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.deposit.tests.test_docsfilters.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filters tests for the base filters system.

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

from __future__ import annotations
import datetime
import unittest
from dataclasses import dataclass

import whakerkit
from whakerkit.filters import FilteredSet
from whakerkit.documents.docs_filters import DocumentsFilters

# ---------------------------------------------------------------------------


@dataclass
class MockFileInfo:
    """Store information on a file with the expected access members.

    """
    author: str
    date: datetime.date
    filename: str
    filetype: str
    description: str | None

    def __hash__(self):
        return hash("_".join([self.author, str(self.date), self.filename, self.filetype]))

# ---------------------------------------------------------------------------


class TestDocumentsFilters(unittest.TestCase):

    def setUp(self):
        self.data = list()
        self.data.append(MockFileInfo(
            author="Brigitte", date=datetime.date(2025, 3, 21),
            filename="test", filetype="txt", description="le doc de brigitte"))
        self.data.append(MockFileInfo(
            author="titi", date=datetime.date(2022, 5, 12),
            filename="compte-rendu", filetype="txt", description=None))
        self.data.append(MockFileInfo(
            author="tito", date=datetime.date(2024, 5, 12),
            filename="présentation", filetype="pptx", description=None))
        self.data.append(MockFileInfo(
            author="toto", date=datetime.date(2022, 5, 12),
            filename="compte-rendu", filetype="docx", description="toto doc"))
        self.data.append(MockFileInfo(
            author="toto", date=datetime.date(2024, 5, 12),
            filename="compte-rendu - Copie", filetype="docx", description="toto compte-rendu"))

    # -----------------------------------------------------------------------

    def test_instantiation(self):
        """Test DocumentsFilters init."""
        f = DocumentsFilters(self.data)
        self.assertIs(f._obj, self.data)

        with self.assertRaises(TypeError):
            obj = [
                {
                    "author": "John",
                    "date": "2022-01-01",
                    "filename": "file1",
                    "filetype": "txt"
                }
            ]
            DocumentsFilters(obj)

        with self.assertRaises(TypeError):
            DocumentsFilters(None)

        with self.assertRaises(TypeError):
            DocumentsFilters(['a', 'b'])

    # -----------------------------------------------------------------------

    def test_author(self):
        """Test DocumentsFilters author."""
        f = DocumentsFilters(self.data)

        result = f.author(exact="Brigitte")
        self.assertIsInstance(result, FilteredSet)
        self.assertEqual(len(result), 1)

        result = f.author(iexact="brigitte")
        self.assertEqual(len(result), 1)

        result = f.author(not_exact="toto")
        self.assertEqual(len(result), 3)

        # and operator
        result1 = f.author(startswith="ti", not_endswith='to', logic_bool="and")
        self.assertEqual(len(result1), 1)
        result2 = f.author(startswith="ti") & f.author(not_endswith='to')
        self.assertEqual(result1, result2)

        # or operator
        result1 = f.author(startswith="ti", not_endswith='to', logic_bool="or")
        self.assertEqual(len(result1), 3)
        result2 = f.author(startswith="ti") | f.author(not_endswith='to')
        self.assertEqual(result1, result2)

    # -----------------------------------------------------------------------

    def test_date(self):
        """Test DocumentsFilters author."""
        f = DocumentsFilters(self.data)

        result = f.date(equal=datetime.date(2024, 5, 12))
        self.assertIsInstance(result, FilteredSet)
        self.assertEqual(len(result), 2)

    # -----------------------------------------------------------------------

    def test_cast_data(self):
        """Test DocumentsFilters cast_data."""
        # the value is a string and the function is expecting a string
        result = DocumentsFilters.cast_data('author', 'John Doe')
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'John' + whakerkit.sg.FIELDS_NAME_SEPARATOR+'Doe')

        # the value is not a string and the function is expecting a string
        result = DocumentsFilters.cast_data('author', True)
        self.assertIsInstance(result, str)
        self.assertEqual(result, 'True')
        result = DocumentsFilters.cast_data('filename', 123)
        self.assertIsInstance(result, str)
        self.assertEqual(result, '123')

        # the value is not a string and can't be converted and the function is expecting a string
        # to do

        # the value is a valid string and the function is expecting a date
        result = DocumentsFilters.cast_data('date', '2023-01-01')
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, datetime.date(2023, 1, 1))

        # the value is an invalid string and the function is expecting a date
        with self.assertRaises(ValueError):
            DocumentsFilters.cast_data('date', '2023-02-30')
        with self.assertRaises(TypeError):
            DocumentsFilters.cast_data('date', None)

        # unknown filter
        with self.assertRaises(KeyError):
            DocumentsFilters.cast_data('unknown_filter', 'value')

    # -----------------------------------------------------------------------

    def test_merge_data(self):
        """Test DocumentsFilters merge_data."""
        # Merge no filtered set
        result = DocumentsFilters.merge_data([], match_all=False)
        self.assertEqual(result, FilteredSet())

        # Only one filtered set
        fs1 = FilteredSet()
        fs1.append("data1")

        result = DocumentsFilters.merge_data([fs1])
        self.assertIn("data1", result)
        self.assertNotIn("data2", result)

        # Two filtered sets
        fs2 = FilteredSet()
        fs2.append("data2")

        # Union (| operator)
        result = DocumentsFilters.merge_data([fs1, fs2], match_all=False)
        self.assertIn("data1", result)
        self.assertIn("data2", result)

        # Add data to FilteredSet
        fs1.append("data2")

        # Union |
        result = DocumentsFilters.merge_data([fs1, fs2], match_all=False)
        self.assertIn("data1", result)
        self.assertIn("data2", result)

        # Intersection &
        result = DocumentsFilters.merge_data([fs1, fs2], match_all=True)
        self.assertIn("data2", result)
        self.assertNotIn("data1", result)

        # test_commutative operations:
        fs1 = FilteredSet()
        fs2 = FilteredSet()
        fs3 = FilteredSet()
        fs1.append("data1")
        fs2.append("data2")
        fs2.append("data1")
        fs3.append("data3")

        # Union operation in different orders
        union_result_1 = DocumentsFilters.merge_data([fs1, fs2, fs3], match_all=False)
        union_result_2 = DocumentsFilters.merge_data([fs3, fs2, fs1], match_all=False)
        self.assertEqual(union_result_1, union_result_2)

        # Intersection operation in different orders -- no common data
        intersection_result_1 = DocumentsFilters.merge_data([fs1, fs2, fs3], match_all=True)
        intersection_result_2 = DocumentsFilters.merge_data([fs3, fs2, fs1], match_all=True)
        self.assertEqual(len(intersection_result_1), 0)
        self.assertEqual(intersection_result_1, intersection_result_2)

        # Then assuming all have common data1 for this example
        fs3.append("data1")
        intersection_result_1 = DocumentsFilters.merge_data([fs1, fs2, fs3], match_all=True)
        intersection_result_2 = DocumentsFilters.merge_data([fs3, fs2, fs1], match_all=True)
        self.assertEqual(len(intersection_result_1), 1)
        self.assertTrue("data1" in intersection_result_1)
        self.assertFalse("data2" in intersection_result_1)
        self.assertFalse("data3" in intersection_result_1)
        self.assertEqual(intersection_result_1, intersection_result_2)

        # Invalid type
        with self.assertRaises(TypeError):
            DocumentsFilters.merge_data([("a",), ("b",)], match_all=True)
        with self.assertRaises(TypeError):
            DocumentsFilters.merge_data(["a", "b"], match_all=True)
