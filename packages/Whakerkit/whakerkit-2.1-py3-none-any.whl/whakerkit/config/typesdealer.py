# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.typesdealer.py
:author: Brigitte Bigi
:contributor: Chiheb Bradai
:contact: contact@sppas.org
:summary: This module provides a set of functions to deal with types.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io
.. _This file was originally part of WhintPy - by Brigitte Bigi, CNRS.
    Integrated into WhakerKit as of 2025-05-23.

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
import re
from datetime import datetime
import unicodedata
import string

from .typesmapping import TypesMapping

# ---------------------------------------------------------------------------


class TypesDealer:
    """Deal with types.

    Provide various functionalities for type conversion, validation, and data
    parsing.

    This class is especially useful for applications that require strict type
    checking and data manipulation.

    ### Features:

    - **Type Validation:** Verify the types of given arguments against expected types.
    - **Type Casting:** Cast values to specified types with support for complex data structures and custom formats.
    - **Data Parsing:** Transform string data into structured lists or tuples.
    - **Data Serialization:** Convert lists or tuples into a concatenated string format.
    - **Type Retrievalidation:** Get the types of elements within a data structure.

    """

    # TypeMapping is used to store the types used in the cast_types method
    __TYPE_MAPPING = TypesMapping()

    # -----------------------------------------------------------------------

    @staticmethod
    def get_instance_type_mapping():
        """Get the instance of the type mapping.

        It can be used to add new types to the mapping.

        :example:
        >>> # Add a new type to the mapping
        >>> type_mapping = TypesDealer.get_instance_type_mapping()
        >>> # Add upper type to the mapping
        >>> type_mapping.add_type('upper', lambda x: x.upper())
        >>> # Cast a string to upper case
        >>> TypesDealer.cast_types("hello", upper)
        >>> output: "HELLO"

        :return: (TypeMapping) instance of the type mapping

        """
        return TypesDealer.__TYPE_MAPPING

    # -----------------------------------------------------------------------

    @staticmethod
    def check_types(function: str, arg_types: list) -> None:
        """Check the given args with their expected types.

        If the types are correct, the function returns None and no error is raised.

        :example:
        >>> TypesDealer.check_types("cool_function", [(2, int), ("description", str), (True, (bool, str)),]
        >>> TypesDealer.check_types("cool_function", [(bool, bool),])
        >>> TypesDealer.check_types("example_function", [(2, int), ("hello", str)])

        :param function: (str) Name of the function where the check is done
        :param arg_types: (list) List of tuples containing the value(s) and its expected type(s)
        :raises: TypeError: If the example does not match the expected type(s).

        """
        if isinstance(function, str) is False:
            raise TypeError(
                f"TypesDealer.check_types exception: function must be a string got {type(function)} instead")
        if isinstance(arg_types, list) is False:
            raise TypeError(
                f"TypesDealer.check_types exception: arg_types must be a list, got {type(arg_types)} instead")

        for arg, expected_types in arg_types:
            if isinstance(expected_types, tuple) is False:
                expected_types = (expected_types,)
            if isinstance(arg, type) is True:
                if arg not in expected_types and type not in expected_types:
                    raise TypeError(f"{function} exception: {arg} is not of type {expected_types}")
            else:
                if isinstance(arg, expected_types) is False:
                    raise TypeError(f"{function} exception: {arg} is not of type {expected_types}")

    # -----------------------------------------------------------------------

    @staticmethod
    def cast_types(value, expected_type, **kwargs):
        """Cast the arguments to the expected types.

        :example:
        >>> # Cast a string to a datetime object (for a specific format,
        >>> # the type must be passed in a keyword argument)
        >>> TypesDealer.cast_types("24-07-2004", datetime, format="%d-%m-%Y")
        "24-07-2004"
        >>> # Using a default format
        >>> TypesDealer.cast_types("2004-07-24", datetime)
        "2004-07-24"
        >>> # Cast a string to an int
        >>> TypesDealer.cast_types("24", int)
        24

        :param value: The value to cast
        :param expected_type: The expected type
        :return: The value cast to the expected type

        """
        allowed_kwargs = {'format'}
        if set(kwargs).issubset(allowed_kwargs) is False:
            raise ValueError(f"TypesDealer.cast_types exception: Invalid keyword argument(s), got {type(kwargs)}.")

        TypesDealer.check_types("TypesDealer.cast_types", [(expected_type, (type, str))])
        date_format = None
        if kwargs.get('format') is not None:
            date_format = kwargs.get('format')
        if isinstance(expected_type, str) is True:
            conversion_function = TypesDealer.__TYPE_MAPPING.get_type(expected_type, date_format)
        else:
            conversion_function = TypesDealer.__TYPE_MAPPING.get_type(expected_type.__name__, date_format)

        # TO DO: complete the condition. if conversion_function WHAT?
        if conversion_function:
            return conversion_function(value)

        raise TypeError(f"TypesDealer.cast_types exception: {expected_type} is not a valid type")

    # ---------------------------------------------------------------------------------------------

    @staticmethod
    def parse_data(data, separator: str, type_to_parse: type(list) | type(tuple) = list):
        """Parse a string of data into a list or a tuple of elements (list by default).

        :example:
        >>> TypesDealer.parse_data("a-b-c-d-e", "-", tuple)
        ('a', 'b', 'c', 'd', 'e')
        >>> TypesDealer.parse_data("1,2,3,4,5", ",")
        ['1', '2', '3', '4', '5']

        :param data: The data to parse
        :param separator: (str) The separator
        :param type_to_parse: The type to parse the data to (list by default)
        :return: The parsed data

        """
        TypesDealer.check_types("TypesDealer.parse_data", [(data, str), (separator, str),
                                                           (type_to_parse, (tuple, list))])
        if separator is None:
            raise TypeError("TypesDealer.parse_data exception: separator cannot be None")
        if separator == "":
            raise ValueError("TypesDealer.parse_data exception: separator cannot be an empty string")
        if data == "":
            if type_to_parse == list:
                return []
            return ()
        data = data.split(separator)
        if type_to_parse == tuple:
            return tuple(data)

        return data

    # ---------------------------------------------------------------------------------------------
    @staticmethod
    def serialize_data(data, separator):
        """Serialize a list or a tuple of elements into a string of data.

        :example:
        >>> TypesDealer.serialize_data(['a', 'b', 'c', 'd', 'e'], "-")
        "a-b-c-d-e"
        >>> TypesDealer.serialize_data(('1', '2', '3', '4', '5'), ",")
        "1,2,3,4,5"

        :param data: The data to serialize
        :param separator: The separator
        :return: The serialized data

        """
        TypesDealer.check_types("TypesDealer.serialize_data", [(data, (list, tuple)), (separator, str)])
        if separator is None:
            raise TypeError("TypesDealer.serialize_data exception: separator cannot be None")
        if separator == "":
            raise ValueError("TypesDealer.serialize_data exception: separator cannot be an empty string")
        data = [TypesDealer.cast_types(elm, str) for elm in data]

        return separator.join(data)

    # ---------------------------------------------------------------------------------------------

    @staticmethod
    def get_types(data):
        """Return the types of the elements in parameter "data".

        :example:
        >>> TypesDealer.get_types([1, "a", True, 2.0])
        {1: class<'int'>, 'a': class<'str'>, True: class<'bool'>, 2.0: class<'float'>}
        >>> TypesDealer.get_types(1)
        {1: class<'int'>}

        :param data: The data to get the types from.
        :return: (dict) types of the elements in the data

        """
        if isinstance(data, (list, tuple)) is False:
            return type(data)
        return {elm: type(elm) for elm in data}

    # ---------------------------------------------------------------------------------------------

    @staticmethod
    def clear_string(entry: str, invalid_characters: str) -> str:
        """Remove invalid characters from a string.

        :example:
        >>> # Remove "," and "!" from the string
        >>> TypesDealer.clear_string("hello, world!", ",!")
        "hello world"
        >>> # Remove invalid characters from a string
        >>> invalid_chars = "!@#$%^&*()_+"
        >>> TypesDealer.clear_string("hello !@#$%^&*()_+ world", invalid_chars)
        "hello  world"

        :param entry: (str) The string to clean
        :param invalid_characters: (str) The characters to remove
        :return: (str) The cleaned string

        """
        TypesDealer.check_types("TypesDealer.clear_string", [(entry, str), (invalid_characters, str)])
        return ''.join([char for char in entry if char not in invalid_characters])

    # -----------------------------------------------------------------------

    @staticmethod
    def strip_string(entry: str) -> str:
        """Strip the string: remove multiple whitespace, tab, and CR/LF.

        :example:
        >>> TypesDealer.strip_string("hello    world ")
        "hello world"
        >>> # Unicode BOM and other zero-width characters
        >>> print(TypesDealer.strip_string("\ufeffHello World"))
        "Hello World"

        :param entry: (str) The string to strip
        :return: (str) The stripped string
        :raises: TypeError: if the entry is not a string

        """
        TypesDealer.check_types("TypesDealer.strip_string", [(entry, str)])
        # Remove zero-width spaces along with other whitespace characters
        entry = re.sub(r"[\s\u200B]+", " ", entry)
        # Strip leading and trailing spaces
        entry = entry.strip()
        # Remove Unicode BOM if present
        entry = entry.replace("\ufeff", "")
        entry = re.sub(r'[\s]+', ' ', entry).strip()

        return entry

    # ----------------------------------------------------------------------------
    @staticmethod
    def clear_whitespace(entry: str, separator: str = "_") -> str:
        """Strip and replace whitespace by a character.

        :example:
        >>> TypesDealer.clear_whitespace("hello    world")
        "hello_world"

        :param entry: (str) The string to clear whitespace from
        :param separator: (str) The character to replace whitespace with
        :raises: TypeError: if the entry is not a string
        :return: (str) The string with whitespace replaced by underscores

        """
        TypesDealer.check_types("TypesDealer.clear_whitespace", [(entry, str)])
        e = TypesDealer.strip_string(entry)
        e = re.sub(r'\s', separator, e)
        return e

    # -----------------------------------------------------------------------

    @staticmethod
    def to_ascii(entry: str) -> str:
        """Replace the non-ASCII characters by underscores.

        :example:
        >>> # with diacritics
        >>> TypesDealer.to_ascii("Café Münster—☆")
        "Caf_ M_nster__"
        >>> # With emojis
        >>> print(TypesDealer.to_ascii("😊🎉🚀"))
        "___"

        :param entry: (str) The entry to process
        :raises: TypeError: if the entry is not a string
        :return: (str) The entry with non-ASCII characters replaced by underscores

        """
        TypesDealer.check_types("TypesDealer.to_ascii", [(entry, str)])
        for char in entry:
            if ord(char) > 127:
                entry = entry.replace(char, "_")
        return entry

    # -----------------------------------------------------------------------

    @staticmethod
    def is_restricted_ascii(entry: str) -> bool:
        """Check if the entry key is using only a-Z0-9 characters.

        :example:
        >>> TypesDealer.is_restricted_ascii("hello_world")
        True
        >>> TypesDealer.is_restricted_ascii("hello world")
        False
        >>> # With emojis
        >>> print((TypesDealer.is_restricted_ascii("😊🎉🚀")))
        False

        :param entry: (str) The entry to check
        :raises: TypeError: if the entry is not a string
        :return: (bool) True if the entry key is using only a-Z0-9 characters, False otherwise

        """
        TypesDealer.check_types("TypesDealer.is_restricted_ascii", [(entry, str)])
        return re.match(r'^[a-zA-Z0-9_]*$', entry) is not None

    # -----------------------------------------------------------------------

    @staticmethod
    def remove_diacritics_and_non_ascii(entry: str) -> str:
        """Remove the diacritics and non-ASCII characters from a string.

        :example:
        >>> TypesDealer.remove_diacritics_and_non_ascii("éèàç")
        "eeca"
        >>> TypesDealer.remove_diacritics_and_non_ascii("São Tomé and Príncipe 日本語")
        "Sao Tome and Principe"

        :param entry: (str) The string to process
        :return: (str) The string without diacritics and non-ASCII characters

        """
        TypesDealer.check_types("TypesDealer.remove_diacritics_and_non_ascii", [(entry, str)])

        # Mapping of special characters to their ASCII equivalents
        special_char_map = {
            'ç': 'c', 'Ç': 'C', 'ø': 'o', 'Ø': 'O', 'œ': 'oe', 'Œ': 'OE',
            'ß': 'ss', 'ñ': 'n', 'Ñ': 'N', 'á': 'a', 'Á': 'A', 'à': 'a', 'À': 'A',
            'â': 'a', 'Â': 'A', 'ä': 'a', 'Ä': 'A', 'ã': 'a', 'Ã': 'A', 'å': 'a',
            'Å': 'A', 'æ': 'ae', 'Æ': 'AE', 'é': 'e', 'É': 'E', 'è': 'e', 'È': 'E',
            'ê': 'e', 'Ê': 'E', 'ë': 'e', 'Ë': 'E', 'í': 'i', 'Í': 'I', 'ì': 'i',
            'Ì': 'I', 'î': 'i', 'Î': 'I', 'ï': 'i', 'Ï': 'I', 'ó': 'o', 'Ó': 'O',
            'ò': 'o', 'Ò': 'O', 'ô': 'o', 'Ô': 'O', 'ö': 'o', 'Ö': 'O', 'õ': 'o',
            'Õ': 'O', 'ú': 'u', 'Ú': 'U', 'ù': 'u', 'Ù': 'U', 'û': 'u', 'Û': 'U',
            'ü': 'u', 'Ü': 'U', 'ý': 'y', 'Ý': 'Y', 'ÿ': 'y', 'Ÿ': 'Y'
        }

        # Replace special characters using the mapping
        entry = ''.join(special_char_map.get(c, c) for c in entry)
        # Normalize the string to decompose characters
        entry = unicodedata.normalize('NFD', entry)
        # Remove the diacritics
        entry = ''.join(c for c in entry if unicodedata.category(c) != 'Mn')
        # Remove non-ASCII characters
        entry = ''.join(c for c in entry if
                        c in string.ascii_letters or c in string.digits or c in string.punctuation
                        or c in string.whitespace)

        return entry
