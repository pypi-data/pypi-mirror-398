# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.deposit.tests.test_documents_manager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Test DocumentsManager

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
from unittest.mock import patch
from unittest.mock import MagicMock
from unittest.mock import mock_open

from whakerkit.documents.document import Document
from whakerkit.documents.document import ImmutableDocument
from whakerkit.documents.docs_manager import DocumentsManager

# ---------------------------------------------------------------------------


class TestDocumentsManager(unittest.TestCase):

    @patch('os.path.exists')
    def setUp(self, mock_exists):
        mock_exists.return_value = True
        self.folder_path = "test_folder"
        self.manager = DocumentsManager(self.folder_path)

    # -----------------------------------------------------------------------

    @patch('os.path.exists')
    def test_init(self, mock_exists):
        """Test the constructor with both valid and invalid folder paths."""
        # Valid folder
        mock_exists.return_value = True
        manager = DocumentsManager(self.folder_path)
        self.assertEqual(manager.get_folder_path(), self.folder_path)

        # No specific folder is given. Use '' by default.
        manager = DocumentsManager()
        self.assertEqual(manager.get_folder_path(), ".")

        # Invalid folder
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            DocumentsManager("invalid_folder")

        # with invalid type
        with self.assertRaises(TypeError):
            DocumentsManager(123)

    # -----------------------------------------------------------------------

    @patch('os.path.exists')
    @patch('os.scandir')
    @patch('builtins.open', new_callable=mock_open, read_data='This is a description')
    def test_collect_docs(self, mock_open, mock_scandir, mock_exists):
        """Test collect_docs under different file system scenarios."""
        folder_base = '/path/to/test_folder'
        valid_folder_name = 'author_2024-05-16_filetype_filename'

        # Mock directory entries for os.scandir
        mock_dir_entry = MagicMock()
        mock_dir_entry.is_dir.return_value = True
        mock_dir_entry.name = valid_folder_name
        mock_dir_entry.path = f'{folder_base}/{valid_folder_name}'

        # Scenario 1: Assume the folder exists and has valid directories
        mock_exists.side_effect = lambda path: True if path == self.folder_path or path.endswith(
            'description.txt') else False
        mock_scandir.return_value = [mock_dir_entry]

        self.manager.collect_docs()
        self.assertGreater(len(self.manager), 0)

        # Reset mocks for the next scenario
        mock_exists.reset_mock()
        mock_open.reset_mock()

        # Scenario 2: Assume the folder does not exist
        mock_exists.side_effect = lambda path: False

        with self.assertRaises(FileNotFoundError):
            self.manager.collect_docs()

    # -----------------------------------------------------------------------

    def test_get_doc_content(self):
        """Test getting document content."""
        # Document is in the list
        doc = Document('doc1', 'doc1.txt', datetime.datetime.now())
        self.manager.add_doc(doc)
        with patch('builtins.open', mock_open(read_data='content')), patch('os.path.exists', return_value=True):
            self.assertEqual(self.manager.get_doc_content(doc), 'content')

        # No documents collected
        self.manager.clear_docs()
        with self.assertRaises(AttributeError):
            self.manager.get_doc_content(doc)

    # -----------------------------------------------------------------------

    def test_docs_list_methods(self):
        """Test getting all documents and checking document presence."""
        # Assume documents are in the list
        doc = Document('doc1', 'doc1.txt', datetime.datetime.now())
        another_doc = Document('doc2', 'doc2.txt', datetime.datetime.now())
        self.manager.add_doc(doc)
        # Test if the document is in the list
        self.assertIn(doc, self.manager)
        # Test if the document is not in the list
        self.assertNotIn(another_doc, self.manager)

    # -----------------------------------------------------------------------

    def test_add(self):
        """Test adding a document to the list."""
        pass
        # manager = DocumentsManager() # we should be able to do this...
        # doc = manager.add("doc1", "doc1.txt")
        # self.assertIn(doc, manager.get_all_docs())
        # TO DO

    # -----------------------------------------------------------------------

    def test_add_doc(self):
        """Test adding a document to the list."""
        # Test adding a Document object
        doc = Document('doc1', 'doc1.txt', date=datetime.datetime.now())
        self.manager.add_doc(doc)
        self.assertIn(doc, self.manager)

        # Test adding a non-Document object
        with self.assertRaises(TypeError):
            self.manager.add_doc('doc1')

    # -----------------------------------------------------------------------

    def test_add_docs(self):
        """Test adding multiple documents to the list."""
        doc1 = Document('author1', 'doc1.txt', datetime.datetime(2023, 5, 20))
        doc2 = Document('author2', 'doc2.txt', datetime.datetime(2024, 1, 1))
        docs = [doc1, doc2]
        self.manager.add_docs(docs)
        self.assertIn(doc1, self.manager)
        self.assertIn(doc2, self.manager)
        self.assertEqual(len(self.manager), 2)

    # -----------------------------------------------------------------------

    def test_clear_doc(self):
        """Test clearing the list of documents."""
        doc = Document('doc1', 'doc1.txt', datetime.datetime.now())
        self.manager.add_doc(doc)
        self.manager.clear_docs()
        self.assertEqual(len(self.manager), 0)

    # -----------------------------------------------------------------------

    def test_get_docs_sorted_by_newest(self):
        """Test getting documents sorted by newest first."""
        doc1 = Document('author1', 'doc1.txt', datetime.datetime(2023, 5, 20))
        doc2 = Document('author2', 'doc2.txt', datetime.datetime(2024, 1, 1))
        doc3 = Document('author3', 'doc3.txt', datetime.datetime(2022, 12, 25))
        self.manager.add_doc(doc1)
        self.manager.add_doc(doc2)
        self.manager.add_doc(doc3)

        sorted_docs = self.manager.get_docs_sorted_by_newest()
        self.assertEqual(sorted_docs, [doc2, doc1, doc3])

    # -----------------------------------------------------------------------

    def test_get_docs_sorted_by_oldest(self):
        """Test getting documents sorted by oldest first."""
        doc1 = Document('author1', 'doc1.txt', datetime.datetime(2023, 5, 20))
        doc2 = Document('author2', 'doc2.txt', datetime.datetime(2024, 1, 1))
        doc3 = Document('author3', 'doc3.txt', datetime.datetime(2022, 12, 25))
        self.manager.add_doc(doc1)
        self.manager.add_doc(doc2)
        self.manager.add_doc(doc3)

        sorted_docs = self.manager.get_docs_sorted_by_oldest()
        self.assertEqual(sorted_docs, [doc3, doc1, doc2])

    # -----------------------------------------------------------------------

    def test_get_docs_sorted_by_most_viewed(self):
        """Test getting documents sorted by most viewed first."""
        doc1 = Document('author1', 'doc1.txt', datetime.datetime(2023, 5, 20))
        doc2 = Document('author2', 'doc2.txt', datetime.datetime(2024, 1, 1))
        doc3 = Document('author3', 'doc3.txt', datetime.datetime(2022, 12, 25))

        # Mock the number of downloads
        with patch.object(Document, 'get_downloads', side_effect=[10, 30, 20]):
            self.manager.add_doc(doc1)
            self.manager.add_doc(doc2)
            self.manager.add_doc(doc3)

            sorted_docs = self.manager.get_docs_sorted_by_most_viewed()
            self.assertEqual(sorted_docs, [doc2, doc3, doc1])

    # -----------------------------------------------------------------------

    def test_get_docs_sorted_by_least_viewed(self):
        """Test getting documents sorted by least viewed first."""
        doc1 = Document('author1', 'doc1.txt', datetime.datetime(2023, 5, 20))
        doc2 = Document('author2', 'doc2.txt', datetime.datetime(2024, 1, 1))
        doc3 = Document('author3', 'doc3.txt', datetime.datetime(2022, 12, 25))

        # Mock the number of downloads
        with patch.object(Document, 'get_downloads', side_effect=[10, 30, 20]):
            self.manager.add_doc(doc1)
            self.manager.add_doc(doc2)
            self.manager.add_doc(doc3)

            sorted_docs = self.manager.get_docs_sorted_by_least_viewed()
            self.assertEqual(sorted_docs, [doc1, doc3, doc2])

    # -----------------------------------------------------------------------

    @patch('os.path.exists')
    def test_filter_docs(self, mock_exists):
        """Test filtering documents."""
        mock_exists.return_value = True

        # Single attribute filter
        # =======================

        # Filtering on author
        # -------------------
        manager = DocumentsManager('test_folder')
        manager._DocumentsManager__docs = [
            Document('John Doe', 'doc1.txt', datetime.date(2023, 1, 1)),
            Document('Jane Doe', 'doc2.pdf', datetime.date(2024, 5, 1)),
            Document('Jane Doe', 'doc3.png', datetime.date(2024, 5, 1))
        ]
        filters = [("author", "iexact", ["John Doe"])]
        expected_docs = [manager._DocumentsManager__docs[0]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("author", "startswith", ["Jane"])]
        expected_docs = [manager._DocumentsManager__docs[1], manager._DocumentsManager__docs[2]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("author", "contains", ["Doe"])]
        expected_docs = [manager._DocumentsManager__docs[0], manager._DocumentsManager__docs[1],
                         manager._DocumentsManager__docs[2]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("author", "exact", ["Someone"])]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, [])

        # Filtering on filetype
        # ---------------------

        filters = [("filetype", "iexact", ["txt"])]
        expected_docs = [manager._DocumentsManager__docs[0]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("filetype", "exact", [".TXT"])]
        expected_docs = [manager._DocumentsManager__docs[0]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("filetype", "contains", ["jpg"])]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, [])

        filters = [("filetype", "contains", ["jpg", "png"])]
        expected_docs = [manager._DocumentsManager__docs[2]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        # Filtering on date
        # -----------------
        filters = [("date", "before", ["2024-01-01"])]
        expected_docs = [manager._DocumentsManager__docs[0]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("date", "after", ["2024-01-01"])]
        expected_docs = [manager._DocumentsManager__docs[1], manager._DocumentsManager__docs[2]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("date", "equal", ["2024-05-01"])]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("date", "after", ["2025-01-01"])]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, [])

        # Filtering on filename
        # ---------------------

        filters = [("filename", "contains", ["doc"])]
        expected_docs = [manager._DocumentsManager__docs[0], manager._DocumentsManager__docs[1],
                         manager._DocumentsManager__docs[2]]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, expected_docs)

        filters = [("filename", "not_contains", ["doc"])]
        filtered_docs = manager.filter_docs(filters)
        self.assertEqual(filtered_docs, [])

        # Several attribute filters
        # ========================

        # TO DO

        # Malformed filters
        # ========================

        # no value
        filters = [("filename", "startswith", "")]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)
        filters = [("filename", "startswith", None)]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)

        # no comparator
        filters = [("filename", "", "value")]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)
        filters = [("filename", None, "value")]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)

        # no function
        filters = [("", "iexact", "value")]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)
        filters = [(None, "iexact", "value")]
        with self.assertRaises(ValueError):
            manager.filter_docs(filters)

    # -----------------------------------------------------------------------

    def test_readme_sample(self):
        """Test the sample of the README.md file."""
        # Create 3 documents
        doc1 = Document("Sarah Connor", "Terminator's target.png", date=datetime.date(1984, 5, 12))
        doc2 = Document("T-800", "I'll be back.pptx", date=datetime.date(1984, 5, 12))
        doc3 = Document("Skynet", "JudgementDay.txt", date=datetime.date(1997, 8, 29))
        self.assertEqual(doc1.author, "Sarah_Connor")
        self.assertEqual(doc1.filename, "Terminators_target")

        # Create a manager and add all 3 documents in once
        with patch('os.path.exists', return_value=True):
            manager = DocumentsManager('test_folder')
            manager.add_docs([doc1, doc2, doc3])

        # Add a 4th document
        doc4 = manager.add("Dani Ramos", "Dark Fate.mp4", date=datetime.date.today(),
                           description="The Resistance sends Grace, an augmented soldier, back in time to defend Dani, who is also joined by Sarah Connor and Skynet's T-800.")

        # Convert ImmutableDocument to Document for comparison
        added_doc4 = Document("Dani Ramos", "Dark Fate.mp4", date=datetime.date.today(),
                              description="The Resistance sends Grace, an augmented soldier, back in time to defend Dani, who is also joined by Sarah Connor and Skynet's T-800.")

        self.assertIn(added_doc4, manager.get_docs_sorted_by_oldest())
        self.assertEqual(doc4.author, "Dani_Ramos")

        # ---------------------------
        # Get access to the documents
        # ---------------------------

        # The most recent
        most_recent = manager.get_docs_sorted_by_newest()[0]
        self.assertEqual(most_recent.author, "Dani_Ramos")
        self.assertEqual(most_recent.filename, "Dark_Fate")

        # The oldest
        oldest = manager.get_docs_sorted_by_oldest()[0]
        self.assertIn(oldest, (doc1, doc2))
        self.assertEqual(oldest.date, datetime.date(1984, 5, 12))

    # ---------------------------------------------------------------------------

    def test_invalidate_doc(self):
        """Test deleting and removing documents with various scenarios."""
        # Document exists in the list
        doc = Document('doc1', 'doc1.txt', datetime.datetime.now())
        doc1 = Document('doc2', 'doc2.txt', datetime.datetime.now())
        self.manager.add_doc(doc)

        self.manager.invalidate_doc(doc)
        self.assertNotIn(doc, self.manager)

        # Document not found
        self.manager.add_doc(doc1)
        with self.assertRaises(ValueError):
            self.manager.invalidate_doc(doc)

        # No documents collected
        self.manager.clear_docs()
        with self.assertRaises(AttributeError):
            self.manager.invalidate_doc(doc)

        # Invalid document type
        self.manager.add_doc(doc)
        with self.assertRaises(TypeError):
            self.manager.invalidate_doc("not_a_document")

    # ---------------------------------------------------------------------------

    def test_set_description(self):
        """Test setting a document description with various scenarios."""
        doc = Document('doc1', 'doc1.txt', datetime.date.today())

        self.manager.add_doc(doc)
        new_description = "This is a new description"

        # Document not found scenario
        doc_not_found = Document('doc2', 'doc2.txt', datetime.datetime.now())
        with self.assertRaises(ValueError) as context:
            self.manager.set_doc_description(doc_not_found, new_description)
        self.assertEqual(str(context.exception), "DocumentManager.set_description exception: Document doc2 not found.")

        # No documents collected scenario
        self.manager.clear_docs()
        with self.assertRaises(AttributeError) as context:
            self.manager.set_doc_description(doc, new_description)
        self.assertEqual(str(context.exception),
                         "DocumentManager.set_description exception: No documents found. collect_docs() should be called first.")

        # Invalid document type scenario
        self.manager.add_doc(doc)
        with self.assertRaises(TypeError) as context:
            self.manager.set_doc_description("not_a_document", new_description)
        self.assertEqual(str(context.exception),
                         "DocumentManager.delete exception: not_a_document is not of type (<class 'whakerkit.deposit.document.Document'>, <class 'whakerkit.deposit.document.ImmutableDocument'>)")

    # ---------------------------------------------------------------------------

    def test_increment_doc_downloads(self):
        """Test incrementing the number of downloads for documents under various scenarios."""
        # Document exists in the list
        doc = Document('doc1', 'doc1.txt', datetime.date.today())
        self.manager.add_doc(doc)

        # Document not found
        doc_not_found = Document('doc2', 'doc2.txt', datetime.datetime.now(), 'txt')
        with self.assertRaises(AttributeError):
            self.manager.increment_doc_downloads(doc_not_found)

        # No documents collected
        self.manager.clear_docs()
        with self.assertRaises(AttributeError):
            self.manager.increment_doc_downloads(doc)

        # Invalid document type
        self.manager.add_doc(doc)
        with self.assertRaises(TypeError):
            self.manager.increment_doc_downloads("not_a_document")

    # ---------------------------------------------------------------------------

    def test_save_doc(self):
        """Test saving a document with various scenarios."""
        # Initialize a Document object
        doc = Document('doc1', 'doc1.txt', datetime.datetime.now())
        self.manager.add_doc(doc)

        # Invalid document type scenario
        with self.assertRaises(Exception) as context:
            self.manager.save_doc("not_a_document")

    # ---------------------------------------------------------------------------------

    def test_find_document(self):
        manager = DocumentsManager()
        doc1 = Document("Alice", "Doc1.txt", date=datetime.datetime(2023, 1, 1), content="Sample content")
        manager.add_doc(doc1)
        found_doc = manager._DocumentsManager__find_doc(doc1)
        self.assertEqual(found_doc, doc1)

        doc = ImmutableDocument("Alice", "Doc1.txt", datetime.datetime(2023, 1, 1))
        self.assertTrue(doc1 == doc)

        found_doc = manager._DocumentsManager__find_doc(doc)
        self.assertEqual(found_doc, doc1)

        doc_not_found = Document('doc2', 'doc2.txt', datetime.datetime.now())
        found_doc = manager._DocumentsManager__find_doc(doc_not_found)
        self.assertIsNone(found_doc)

    # ---------------------------------------------------------------------------------

    def test_immutable_to_document(self):
        manager = DocumentsManager()
        idoc = ImmutableDocument("Alice", "Doc1.txt", date=datetime.datetime(2023, 1, 1), content="Sample content")
        manager.add_doc(idoc)
        doc = manager._DocumentsManager__immutable_to_document(idoc)
        self.assertTrue(doc == idoc)
