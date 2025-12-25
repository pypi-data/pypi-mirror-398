# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.deposit.tests.test_document.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test Document() class

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

import copy
import os
import shutil
import unittest
import datetime

import whakerkit
from whakerkit.documents.document import Document
from whakerkit.documents.document import ImmutableDocument

# ---------------------------------------------------------------------------


class TestImmutableDocument(unittest.TestCase):

    def test_immutable_init(self):
        doc = ImmutableDocument(
            author="Alice",
            filename="Doc1.pdf",
            date=datetime.date(2024, 1, 1),
            content="a cool content"
        )
        self.assertEqual(doc.author, "Alice")
        self.assertEqual(doc.filename, "Doc1")
        self.assertEqual(doc.filetype, "pdf")
        with self.assertRaises(AttributeError):
            doc.author = "Bob"
        with self.assertRaises(AttributeError):
            del doc.author

# ---------------------------------------------------------------------------


class TestDocument(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_uploads"
        os.makedirs(self.test_dir, exist_ok=True)

        self.author = "Test"
        self.filename = "testDocument.txt"
        self.content = "This is a test document."
        self.filetype = "txt"
        self.description = "This is a test description."
        self.date = datetime.date(2024, 1, 1)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    # -----------------------------------------------------------------------

    def test_initialization(self):
        """Test document initialization."""
        # Test successful initialization
        doc = Document(self.author, self.filename)
        self.assertEqual(doc._Document__author, self.author)
        self.assertEqual(doc._Document__filename, "testDocument")
        self.assertEqual(doc._Document__filetype, "txt")
        self.assertIsNotNone(doc._Document__date)  # automatically assigned
        self.assertEqual(doc._Document__content, "")

        # Test initialize with kwargs
        kwargs = {"content": self.content, "date": self.date}
        doc = Document(self.author, self.filename, **kwargs)
        self.assertEqual(doc._Document__author, self.author)
        self.assertEqual(doc._Document__filename, "testDocument")
        self.assertEqual(doc._Document__filetype, "txt")
        self.assertEqual(doc._Document__date, self.date)
        self.assertEqual(doc._Document__content, self.content)
        # Test initialization with empty filename
        with self.assertRaises(ValueError):
            Document(self.author, "", self.date, self.content, self.filetype)

        # Test initialization with empty author
        with self.assertRaises(ValueError):
            Document("", self.filename, self.date, self.content, self.filetype)

        # Test filename handling
        doc = Document("invl/d$^ authoré", "inv a/lid:na*meè.txt", self.date, self.content, self.filetype)
        self.assertEqual(doc._Document__filename, "inv" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"alidnameè")
        self.assertEqual(doc._Document__author, "invld" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"authoré")

        # Test filename length boundary
        with self.assertRaises(ValueError):
            Document(self.author, "abc", self.date, self.content, self.filetype)
        doc = Document(self.author, "abcd", self.date, self.content, self.filetype)
        self.assertEqual(doc._Document__filename, "abcd")

        # Test file extension extraction
        doc = Document(self.author, "report.pdf", self.date, self.content)
        self.assertEqual(doc._Document__filetype, "pdf")

        # Test filename with special characters
        special_filename = "test@#$.txt"
        doc = Document(self.author, special_filename, self.date, self.content, self.filetype)
        self.assertEqual(doc._Document__filename, "test")

        # With invalid types
        with self.assertRaises(TypeError):
            Document(123, self.filename, content=self.content)
        with self.assertRaises(TypeError):
            Document(self.author, 456,content= self.content)

    # -----------------------------------------------------------------------

    def test_to_immutable_with_empty_content(self):
        doc = Document("Jane Doe-Doe", "empty content.txt", date=datetime.date(2023, 1, 1))
        immutable_doc = doc.to_immutable()
        self.assertEqual(immutable_doc.author, "Jane" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"Doe-Doe")
        self.assertEqual(immutable_doc.filename, "empty" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"content")
        self.assertEqual(immutable_doc.content, "")
        self.assertEqual(immutable_doc.date, datetime.date(2023, 1, 1))
        self.assertEqual(immutable_doc.filetype, "txt")
        self.assertEqual(immutable_doc.description, "")

    # -----------------------------------------------------------------------
    # TO DO: test all getters
    # TO DO: test set_description
    # -----------------------------------------------------------------------

    def test_create_document_by_folder_name(self):
        """Test conversion from folder name to Document object."""
        sep = whakerkit.sg.FOLDER_NAME_SEPARATOR
        folder_name = sep.join(("firstname_last-name", "2022_05_20", "pdf", "Compte_rendu_réunion"))
        doc = Document.create_document_by_folder_name(folder_name)
        self.assertEqual(doc.author, "firstname_last-name")
        self.assertEqual(doc.filename, "Compte_rendu_réunion")
        self.assertEqual(doc.filetype, "pdf")
        self.assertEqual(doc.date, datetime.date(2022, 5, 20))
        self.assertEqual(doc.content, "")
        self.assertEqual(doc.description, "")
        self.assertEqual(doc.downloads, 0)

        # TO DO: test with various invalid folder fields
        # TO DO: test with invalid types (None, etc)

    # -----------------------------------------------------------------------

    def test_increment_downloads(self):
        """Test incrementing the number of downloads of the document."""
        doc = Document(self.author, self.filename, self.date)

        # Increment the downloads count and verify the value
        self.assertEqual(doc.increment_downloads(), 1)
        self.assertEqual(doc.increment_downloads(), 2)

    # -----------------------------------------------------------------------

    def test_get_content(self):
        """Test getting the content of the document."""
        # Test with string content
        doc_str = Document(self.author, self.filename, content=self.content)
        self.assertEqual(doc_str.get_content(), self.content)

        # Test with bytes content
        content_bytes = b"This is a test document in bytes."
        doc_bytes = Document(self.author, self.filename, self.date, content=content_bytes)
        self.assertEqual(doc_bytes.get_content(), content_bytes)

    # -----------------------------------------------------------------------

    def test_get_description(self):
        """Test retrieving the description of the document."""
        # Create and save a document with a description
        doc = Document(self.author, self.filename, self.date, description=self.description)
        self.assertEqual(doc.get_description(), self.description)

    # -----------------------------------------------------------------------

    def test_readme_sample(self):
        """Test the sample of the README.md file."""
        doc1 = Document("Sarah Connor", "Terminator's target.png", datetime.date(1984, 5, 12))
        doc2 = Document("T-800", "I'll be back.pptx", datetime.date(1984, 5, 12))
        doc3 = Document("Skynet", "JudgementDay.txt", datetime.date(1997, 8, 29))
        self.assertEqual(doc1.author, "Sarah" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"Connor")
        self.assertEqual(doc1.filename, "Terminators" + whakerkit.sg.FIELDS_NAME_SEPARATOR+"target")
        self.assertEqual(doc2.filename, "Ill" + whakerkit.sg.FIELDS_NAME_SEPARATOR + "be" + whakerkit.sg.FIELDS_NAME_SEPARATOR + "back")
        self.assertEqual(doc3.date, datetime.date(1997, 8, 29))

    # -----------------------------------------------------------------------

    def test_repr(self):
        """Test string representation of a document."""
        doc = Document(self.author, self.filename, self.date)
        expected_str = "Document(author=Test, filename=testDocument, date=2024-01-01, filetype=txt)"
        self.assertEqual(repr(doc), expected_str)

    def test_str(self):
        """Test string representation of a document."""
        doc = Document(self.author, self.filename, self.date, self.filetype)
        expected_str = "Document(Test, testDocument, 2024-01-01, txt)"
        self.assertEqual(str(doc), expected_str)

    def test_equal(self):
        """Test comparing two documents."""
        doc1 = Document(self.author, self.filename, self.date, self.content)
        doc2 = Document(self.author, self.filename, date=self.date)
        doc3 = doc2.to_immutable()
        self.assertTrue(doc1 == doc1)
        self.assertTrue(doc1 == copy.deepcopy(doc1))
        self.assertFalse(doc1 == None)
        # The two instances are sharing: author, filename, filetype and date.
        self.assertTrue(doc1 == doc2)
        self.assertTrue(doc2 == doc3)

        doc4 = Document(self.author, self.filename)
        # The two instances are sharing: author, filename, filetype but not date.
        self.assertFalse(doc1 == doc4)
