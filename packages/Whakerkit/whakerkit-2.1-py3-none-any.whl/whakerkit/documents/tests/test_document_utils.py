# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.deposit.tests.test_document_utils.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filters tests for document utilities

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
import datetime

import whakerkit
from whakerkit.documents.document_utils import DocumentUtils

# ---------------------------------------------------------------------------


class TestDocumentUtils(unittest.TestCase):

    def test_get_filetype(self):
        """Test extraction of file extension."""
        self.assertEqual(DocumentUtils.get_filetype("example.txt"), "txt")
        self.assertEqual(DocumentUtils.get_filetype("example."), "")
        self.assertEqual(DocumentUtils.get_filetype("example"), "")
        self.assertEqual(DocumentUtils.get_filetype(".htaccess"), "htaccess")

    def test_format_date(self):
        """Test formatting date."""
        # Date unchanged
        input_date = datetime.date(2023, 3, 15)
        result = DocumentUtils.format_date(input_date)
        self.assertEqual(result, input_date)

        # Datetime to date conversion
        input_datetime = datetime.datetime(2023, 3, 15, 14, 30)
        expected_date = datetime.date(2023, 3, 15)
        result = DocumentUtils.format_date(input_datetime)
        self.assertEqual(result, expected_date)

        # None to date conversion
        result = DocumentUtils.format_date(None)
        expected_date = datetime.date.today()
        self.assertEqual(result, expected_date)

    def test_str_to_date(self):
        """Text to date conversion."""
        result = DocumentUtils.str_to_date("2023-03-15")
        self.assertIsInstance(result, datetime.date)
        self.assertEqual(result, datetime.date(2023, 3, 15))

        # separator is "-"
        result1 = DocumentUtils.str_to_date("1900-01-01")
        result2 = DocumentUtils.str_to_date("9999-12-31")
        self.assertEqual(result1, datetime.date(1900, 1, 1))
        self.assertEqual(result2, datetime.date(9999, 12, 31))

        # separator
        result1 = DocumentUtils.str_to_date("1900_01_01")
        result2 = DocumentUtils.str_to_date("9999_12_31")
        self.assertEqual(result1, datetime.date(1900, 1, 1))
        self.assertEqual(result2, datetime.date(9999, 12, 31))

        with self.assertRaises(ValueError):
            DocumentUtils.str_to_date("03-15-2023")
        with self.assertRaises(ValueError):
            DocumentUtils.str_to_date("2023-02-30")
        with self.assertRaises(ValueError):
            DocumentUtils.str_to_date("2023-01-01 10:00:00")
        with self.assertRaises(ValueError):
            DocumentUtils.str_to_date("2023/01/01")
        with self.assertRaises(ValueError):
            DocumentUtils.str_to_date("January 1, 2023")

    def test_get_folder_name(self):
        """Test folder name generation based on inputs."""
        author = "cool_guy"
        filename = "report"
        date = datetime.datetime(2022, 5, 20)
        filetype = "PDF"
        expected = whakerkit.sg.FOLDER_NAME_SEPARATOR.join(("cool_guy", "2022_05_20", "pdf", "report"))
        self.assertEqual(DocumentUtils.get_folder_name(author, filename, date, filetype), expected)

        author = "Dad Guy-Nice"
        filename = "Report of Yesterday!"
        date = datetime.datetime(2022, 5, 20)
        filetype = "PDF"
        expected = whakerkit.sg.FOLDER_NAME_SEPARATOR.join(("Dad_Guy-Nice", "2022_05_20", "pdf", "Report_of_Yesterday"))
        self.assertEqual(DocumentUtils.get_folder_name(author, filename, date, filetype), expected)

        # TO DO: Test with None for date or filetype
