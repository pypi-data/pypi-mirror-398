# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.tests.test_typesmapping.py
:author: Brigitte Bigi
:contributor: Chiheb Bradai
:contact: contact@sppas.org
:summary: Tests of TypesMapping class

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io
.. _This file was originally part of WhintPy - by Brigitte Bigi, CNRS.
    Integrated into WhakerKit as of 2025-05-23.

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

from whakerkit.config.typesmapping import TypesMapping


class TestTypesMapping(unittest.TestCase):

    def test_initialize(self):
        """Test TypesMapping initialization."""
        # Test successful initialization
        all_types_when_initialized = ('int', 'str', 'bool', 'float', 'list', 'dict', 'tuple', 'datetime', 'date')
        types_mapping = TypesMapping()
        for key, value in types_mapping.__dict__.items():
            self.assertIn(key, all_types_when_initialized)
        self.assertIsInstance(types_mapping, TypesMapping)

    # -----------------------------------------------------------------------

    def test_get_type(self):
        """Test getting conversion functions for different types."""
        types_mapping = TypesMapping()

        # Testing retrieval of default types
        self.assertTrue(callable(types_mapping.get_type('int')))
        self.assertTrue(callable(types_mapping.get_type('bool')))
        self.assertIsNone(types_mapping.get_type('nonexistent'))

        # Testing invalid type_name type raises TypeError
        with self.assertRaises(TypeError):
            types_mapping.get_type(123)

        # Testing date handling with custom format
        custom_date = '2022-01-01'
        datetime_func = types_mapping.get_type('datetime', '%Y-%m-%d')
        self.assertEqual(datetime_func(custom_date), '2022-01-01')

        # Testing date handling with default format
        date_func = types_mapping.get_type('date')
        self.assertEqual(date_func(custom_date), '2022-01-01')

        # Test getting types with unusual or boundary inputs
        self.assertIsNone(types_mapping.get_type(''))
        self.assertIsNone(types_mapping.get_type('a' * 1000))

    # -----------------------------------------------------------------------

    def test_add_conversion(self):
        """Test adding new conversion functions and handle errors."""
        types_mapping = TypesMapping()

        # Testing None as conversion function raises an error
        with self.assertRaises(TypeError):
            types_mapping.add_conversion('test', None)

        # Testing incorrect type for type_name raises an error
        with self.assertRaises(TypeError):
            types_mapping.add_conversion(19, lambda x: x)

        # Testing None as conversion function raises an error
        with self.assertRaises(TypeError):
            types_mapping.add_conversion('test', None)

        # Testing empty string as conversion function raises an error
        with self.assertRaises(TypeError):
            types_mapping.add_conversion('test', "")

        types_mapping.add_conversion('upper', lambda x: x.upper())
        self.assertEqual(types_mapping.get_type('upper')('hello'), 'HELLO')
        # Adding a conversion for a complex type to handle a specific format
        types_mapping.add_conversion(complex, lambda x: complex(x.replace('i', 'j')))
        self.assertEqual(types_mapping.get_type(complex)('1+2i'), complex(1, 2))

        # Testing adding a conversion function that already exists (just modify)
        types_mapping.add_conversion('upper', lambda x: x.lower())
        self.assertEqual(types_mapping.get_type('upper')('HELLO'), 'hello')

        types_mapping.add_conversion(int, lambda x: x+1)
        self.assertEqual(types_mapping.get_type(int)(1), 2)

        # Testing how custom conversion functions handle malformed input
        types_mapping.add_conversion('reverse', lambda x: x[::-1])
        reverse_func = types_mapping.get_type('reverse')
        self.assertEqual(reverse_func('hello'), 'olleh')
        self.assertEqual(reverse_func(''), '')  # Testing empty string

        # Test adding invalid type name
        with self.assertRaises(TypeError):
            types_mapping.add_conversion(123, lambda x: x)

        with self.assertRaises(TypeError):
            types_mapping.add_conversion(123, "not a function")
