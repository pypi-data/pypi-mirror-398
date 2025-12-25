# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.tests.test_typesdealer.py
:author: Brigitte Bigi
:contributor: Chiheb Bradai
:contact: contact@sppas.org
:summary: Tests of TypesDealer class

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
from datetime import datetime

from whakerkit.config.typesmapping import TypesMapping
from whakerkit.config.typesdealer import TypesDealer


class TestTypesDealerCast(unittest.TestCase):

    # ------------------------------
    # CAST_TYPES
    # ------------------------------
    def test_cast_types(self):
        """Test casting various types to other types
        """
        # Testing casting to basic types
        self.assertEqual(TypesDealer.cast_types("2", int), 2)
        self.assertEqual(TypesDealer.cast_types(2, str), "2")
        self.assertEqual(TypesDealer.cast_types("True", bool), True)
        self.assertEqual(TypesDealer.cast_types("2.0", float), 2.0)
        # Testing casting to collections
        self.assertEqual(TypesDealer.cast_types("ab", list), ['a', 'b'])
        self.assertEqual(TypesDealer.cast_types(12, list), [1, 2])
        self.assertEqual(TypesDealer.cast_types("ab", dict), {'a': 'a', 'b': 'b'})
        self.assertEqual(TypesDealer.cast_types("ab", tuple), ('a', 'b'))
        # Testing casting various types to string
        self.assertEqual(TypesDealer.cast_types(24, str), "24")
        self.assertEqual(TypesDealer.cast_types(True, str), "True")
        self.assertEqual(TypesDealer.cast_types(2.0, str), "2.0")
        self.assertEqual(TypesDealer.cast_types([1, 2], str), "[1, 2]")
        self.assertEqual(TypesDealer.cast_types({"a": 1, "b": 2}, str), "{'a': 1, 'b': 2}")
        self.assertEqual(TypesDealer.cast_types((1, 2), str), "(1, 2)")
        # Testing casting numerical values to boolean
        self.assertEqual(TypesDealer.cast_types(1, bool), True)
        self.assertEqual(TypesDealer.cast_types(0, bool), False)
        self.assertEqual(TypesDealer.cast_types(1.0, bool), True)
        self.assertEqual(TypesDealer.cast_types(0.0, bool), False)
        # Testing casting strings to datetime
        self.assertEqual(TypesDealer.cast_types("2004-07-24", datetime), "2004-07-24")
        self.assertEqual(TypesDealer.cast_types("2004-07-24", datetime), "2004-07-24")
        self.assertEqual(TypesDealer.cast_types("24-07-2004", datetime, format="%d-%m-%Y"), "24-07-2004")
        # Testing casting with invalid formats
        with self.assertRaises(ValueError):
            TypesDealer.cast_types("2024-05-10", datetime, format="invalid-format")

        # Testing casting with invalid kwargs
        with self.assertRaises(ValueError):
            TypesDealer.cast_types("2024-05-10", datetime, fake_kwarg="fake")

        # Testing casting with a custom type mapping
        TypesDealer.get_instance_type_mapping().add_conversion('upper', lambda x: x.upper())
        self.assertEqual(TypesDealer.cast_types("hello", 'upper'), "HELLO")

        TypesDealer.get_instance_type_mapping().add_conversion('reverse', lambda x: x[::-1])
        self.assertEqual(TypesDealer.cast_types("hello", 'reverse'), "olleh")

        # Testing casting with invalid types to trigger exceptions
        with self.assertRaises(TypeError):
            TypesDealer.cast_types("hello", complex)
        with self.assertRaises(ValueError):
            TypesDealer.cast_types("not a date", datetime, format="%Y-%m-%d")
        # Testing casting None and empty strings
        self.assertEqual(TypesDealer.cast_types("", str), "")
        self.assertEqual(TypesDealer.cast_types(None, str), "None")
        # Testing casting large numbers
        self.assertEqual(TypesDealer.cast_types("2147483647", int), 2147483647)
        self.assertEqual(TypesDealer.cast_types("-2147483648", int), -2147483648)

    # ------------------------------
    # GET TYPES
    # ------------------------------
    def test_get_types(self):
        """Test getting types of various collections and single elements
        """
        self.assertEqual(TypesDealer.get_types([1, "a", True, 2.0]), {1: int, 'a': str, True: bool, 2.0: float})
        self.assertEqual(TypesDealer.get_types(1), int)
        self.assertEqual(TypesDealer.get_types("hello"), str)
        self.assertEqual(TypesDealer.get_types(["a", "b", "c"]), {'a': str, 'b': str, 'c': str})
        self.assertEqual(TypesDealer.get_types([100, 200, 300]), {100: int, 200: int, 300: int})
        self.assertEqual(TypesDealer.get_types([]), {})
        self.assertEqual(TypesDealer.get_types(()), {})
        self.assertEqual(TypesDealer.get_types((1, 2, 3)), {1: int, 2: int, 3: int})
        self.assertEqual(TypesDealer.get_types(("a", "b")), {'a': str, 'b': str})

    # ------------------------------
    # CHECK TYPES
    # ------------------------------
    class class_test:
        pass

    def test_check_types(self):
        """Test type checking with correct and incorrect types
        """
        # Testing type checking with correct and incorrect types
        with self.assertRaises(TypeError):
            TypesDealer.check_types("cool_function", [(2, str)])
        with self.assertRaises(TypeError):
            TypesDealer.check_types("cool_function", "test")
        with self.assertRaises(TypeError):
            TypesDealer.check_types("cool_function", [(self.class_test, int)])
        with self.assertRaises(TypeError):
            TypesDealer.check_types(128, [(2, int)])

        try:
            TypesDealer.check_types("cool_function", [(2, int), ("description", str), (True, bool)])
            TypesDealer.check_types("cool_function", [([1, 0], list), ({"key": "value"}, dict), ((1, 0), tuple)])
            TypesDealer.check_types("cool_function", [(self.class_test, self.class_test)])
            TypesDealer.check_types("cool_function", [(complex, (type, str))])
        except TypeError:
            self.fail("TypeError was raised unexpectedly!")

    # ------------------------------
    # PARSE DATA
    # ------------------------------
    def test_parse_data(self):
        # Testing data parsing with different separators and data types
        self.assertEqual(TypesDealer.parse_data("a-b-c-d-e", "-", tuple), ('a', 'b', 'c', 'd', 'e'))
        self.assertEqual(TypesDealer.parse_data("1,2,3,4,5", ","), ['1', '2', '3', '4', '5'])
        self.assertEqual(TypesDealer.parse_data("", ","), [])
        self.assertEqual(TypesDealer.parse_data("12345", ","), ['12345'])
        with self.assertRaises(TypeError):
            TypesDealer.parse_data("1-2-3", None)
        with self.assertRaises(ValueError):
            TypesDealer.parse_data("1-2-3", "")
        with self.assertRaises(TypeError):
            TypesDealer.parse_data("1-2-3", "-", "int")
        # Testing parsing with a specific separator
        self.assertEqual(TypesDealer.parse_data("a#b#c", "#"), ['a', 'b', 'c'])
        # Testing parsing with consecutive separators
        self.assertEqual(TypesDealer.parse_data("a,,b,,c", ","), ['a', '', 'b', '', 'c'])
        # Testing parsing with a separator that is not in the string
        self.assertEqual(TypesDealer.parse_data("a-b-c", ","), ['a-b-c'])
        # Testing with an empty string
        self.assertEqual(TypesDealer.parse_data("", ","), [])

    # ------------------------------
    # SERIALIZE DATA
    # ------------------------------
    def test_serialize_data(self):
        # Testing data serialization with different separators and data types
        self.assertEqual(TypesDealer.serialize_data(['a', 'b', 'c', 'd', 'e'], "-"), "a-b-c-d-e")
        self.assertEqual(TypesDealer.serialize_data([], "-"), "")
        self.assertEqual(TypesDealer.serialize_data([1, 2, 3, 4], ","), "1,2,3,4")
        # Testing serialization with different incorrect types
        with self.assertRaises(TypeError):
            TypesDealer.serialize_data(['a', 'b', 'c'], None)
        with self.assertRaises(ValueError):
            TypesDealer.serialize_data(['a', 'b', 'c'], "")
        with self.assertRaises(TypeError):
            TypesDealer.serialize_data(['a', 'b', 'c'], 123)
        with self.assertRaises(TypeError):
            TypesDealer.serialize_data(123, "-")
        # Testing serialization with a list of different types
        self.assertEqual(TypesDealer.serialize_data([], ","), "")
        self.assertEqual(TypesDealer.serialize_data([1, 'two', 3.0], ","), "1,two,3.0")


    # ------------------------------
    # CLEAR STRING
    # ------------------------------
    def test_clear_string(self):
        # Test with common removals of letters
        self.assertEqual(TypesDealer.clear_string("hello world", "ld"), "heo wor",
                         "Should remove 'l' and 'd' from the string")

        # Test removal of special characters
        self.assertEqual(TypesDealer.clear_string("hello, world!", ",!"), "hello world",
                         "Should remove commas and exclamation marks")

        # Test removal of numerical characters
        self.assertEqual(TypesDealer.clear_string("12345abcdef67890", "0123456789"), "abcdef",
                         "Should remove all digits from the string")

        # Test with no invalid characters to be removed
        self.assertEqual(TypesDealer.clear_string("hello world", "xyz"), "hello world",
                         "Should return the original string as there are no characters to remove")

        # Test with an empty string
        self.assertEqual(TypesDealer.clear_string("", "abc"), "", "Should return an empty string when input is empty")

        # Test with empty invalid characters
        self.assertEqual(TypesDealer.clear_string("hello world", ""), "hello world",
                         "Should return the original string when no invalid characters are specified")

        # Test with all characters being invalid
        self.assertEqual(TypesDealer.clear_string("aaaaa", "a"), "",
                         "Should return an empty string when all characters are invalid")

        # Test type validation to ensure proper type handling
        with self.assertRaises(TypeError):
            TypesDealer.clear_string(123, "abc")
        with self.assertRaises(TypeError):
            TypesDealer.clear_string("hello world", 123)

        # Testing clearing a string that consists only of invalid characters
        self.assertEqual(TypesDealer.clear_string("abc", "abc"), "",
                         "Should return an empty string")
        # Testing clearing a string that consists only of invalid characters
        with self.assertRaises(TypeError):
            TypesDealer.clear_string(123, "abc")

        with self.assertRaises(TypeError):
            TypesDealer.clear_string("hello world", 123)

    # ------------------------------
    # STRIP STRING
    # ------------------------------

    def test_strip_string(self):
        # Typical cases with spaces
        self.assertEqual(TypesDealer.strip_string("  hello  world  "), "hello world")
        self.assertEqual(TypesDealer.strip_string("   "), "")

        # Cases with tabs and newlines
        self.assertEqual(TypesDealer.strip_string("\tHello\nWorld\r\n"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("Hello \ufeffWorld"), "Hello World")
        self.assertEqual(TypesDealer.strip_string(" Hello   World "), "Hello World")
        self.assertEqual(TypesDealer.strip_string("Hello World  "), "Hello World")
        self.assertEqual(TypesDealer.strip_string("  Hello World"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("\n\nHello\n\nWorld\n\n"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("\t\tHello\t\tWorld\t\t"), "Hello World")

        # Edge cases with non-breaking space and other whitespace characters
        self.assertEqual(TypesDealer.strip_string("Hello\u00A0World"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("Hello\u2003World"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("Hello\u3000World"), "Hello World")

        # Unicode BOM and other zero-width characters
        self.assertEqual(TypesDealer.strip_string("\ufeffHello World"), "Hello World")
        self.assertEqual(TypesDealer.strip_string("Hello\u200BWorld"), "Hello World")

        # Mixed whitespace characters
        self.assertEqual(TypesDealer.strip_string("\t Hello   \nWorld \r\n"), "Hello World")

        # Strings with no whitespace modifications needed
        self.assertEqual(TypesDealer.strip_string("HelloWorld"), "HelloWorld")

        # Very long string with multiple spaces
        long_string = " " * 1000 + "Hello World" + " " * 1000
        self.assertEqual(TypesDealer.strip_string(long_string), "Hello World")

        # Check completely empty string
        self.assertEqual(TypesDealer.strip_string(""), "")

        # Check strings made up only of whitespace
        self.assertEqual(TypesDealer.strip_string(" \t\n\r"), "")

    # ------------------------------
    # CLEAR WHITE SPACES
    # ------------------------------

    def test_clear_white_spaces(self):
        # Test basic whitespace removal and replacement
        self.assertEqual(TypesDealer.clear_whitespace("  hello  world  "), "hello_world")
        self.assertEqual(TypesDealer.clear_whitespace("hello    world"), "hello_world")

        # Test tabs and newlines
        self.assertEqual(TypesDealer.clear_whitespace("\tHello\nWorld\r\n"), "Hello_World")

        # Test string with no whitespace
        self.assertEqual(TypesDealer.clear_whitespace("HelloWorld"), "HelloWorld")

        # Test string that is all whitespace
        self.assertEqual(TypesDealer.clear_whitespace(" \t\r\n "), "")

        # Test string with leading and trailing whitespace
        self.assertEqual(TypesDealer.clear_whitespace("  Hello World  "), "Hello_World")

        # Test string with mixed whitespace types
        self.assertEqual(TypesDealer.clear_whitespace(" Hello \tWorld\nNew\rLine "), "Hello_World_New_Line")

        # Test string with Unicode whitespace
        self.assertEqual(TypesDealer.clear_whitespace("Hello\u00A0World"), "Hello_World")

        # Test with Zero-width space
        self.assertEqual(TypesDealer.clear_whitespace("Hello\u200BWorld"), "Hello_World")

        # Test empty string
        self.assertEqual(TypesDealer.clear_whitespace(""), "")

    # ------------------------------
    # TO ASCII
    # ------------------------------
    def test_to_ascii(self):
        # Test with standard ASCII characters
        self.assertEqual(TypesDealer.to_ascii("HelloWorld123"), "HelloWorld123")

        # Test with non-ASCII characters
        self.assertEqual(TypesDealer.to_ascii("Café Münster—☆"), "Caf_ M_nster__")

        # Test with mixed ASCII and non-ASCII characters
        self.assertEqual(TypesDealer.to_ascii("北京hello123"), "__hello123")

        # Test with emojis and other complex characters
        self.assertEqual(TypesDealer.to_ascii("😊🎉🚀"), "___")

        # Test with only non-ASCII characters
        self.assertEqual(TypesDealer.to_ascii("ñóç"), "___")

        # Test with an empty string
        self.assertEqual(TypesDealer.to_ascii(""), "")

        # Test with numeric and punctuation characters (which are ASCII)
        self.assertEqual(TypesDealer.to_ascii("1234567890,.;'[]{}"), "1234567890,.;'[]{}")

        # Test to ensure TypeError is raised when passing non-string types
        with self.assertRaises(TypeError):
            TypesDealer.to_ascii(123)

        with self.assertRaises(TypeError):
            TypesDealer.to_ascii(None)

    # ------------------------------
    # IS RESTRICTED ASCII
    # ------------------------------

    def test_is_restricted_ascii(self):
        # Test valid restricted ASCII strings
        self.assertTrue(TypesDealer.is_restricted_ascii("Hello123"))
        self.assertTrue(TypesDealer.is_restricted_ascii("abc123XYZ"))
        self.assertTrue(TypesDealer.is_restricted_ascii("1234567890"))
        self.assertTrue(TypesDealer.is_restricted_ascii("ABCabc_123"))

        # Test empty string should also return True as it contains no invalid characters
        self.assertTrue(TypesDealer.is_restricted_ascii(""))

        # Test invalid strings containing special characters and spaces
        self.assertFalse(TypesDealer.is_restricted_ascii("Hello World"))
        self.assertFalse(TypesDealer.is_restricted_ascii("abc-123"))
        self.assertFalse(TypesDealer.is_restricted_ascii("123@abc"))
        self.assertFalse(TypesDealer.is_restricted_ascii("!@#$%^&*()"))

        # Test strings containing non-ASCII characters
        self.assertFalse(TypesDealer.is_restricted_ascii("Café"))
        self.assertFalse(TypesDealer.is_restricted_ascii("naïve"))
        self.assertFalse(TypesDealer.is_restricted_ascii("ñoño"))
        self.assertFalse(TypesDealer.is_restricted_ascii("😊🎉🚀"))

        # Ensure TypeError is raised for non-string inputs
        with self.assertRaises(TypeError):
            TypesDealer.is_restricted_ascii(123)
        with self.assertRaises(TypeError):
            TypesDealer.is_restricted_ascii(None)

    # ------------------------------
    # GET INSTANCE TYPE MAPPING
    # ------------------------------

    def test_get_instance_type_mapping(self):
        self.assertTrue(isinstance(TypesDealer.get_instance_type_mapping(), TypesMapping))

    # ------------------------------
    # REMOVE DIACRITICS AND NON ASCII
    # ------------------------------
    def test_remove_diacritics_and_non_ascii(self):
        """Test removing diacritics and non-ASCII characters from strings
        """
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("Café crème brûlée à l'éléphant!"),
                         "Cafe creme brulee a l'elephant!")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("Élève à l'école"), "Eleve a l'ecole")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("Garçon très naïf"), "Garcon tres naif")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("São Tomé and Príncipe"),
                         "Sao Tome and Principe")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("français"), "francais")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("coördinate"), "coordinate")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("Æsir"), "AEsir")
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("日本語"),
                         "")  # Non-ASCII characters should be removed
        self.assertEqual(TypesDealer.remove_diacritics_and_non_ascii("Hello, World!"),
                         "Hello, World!")  # No change expected
