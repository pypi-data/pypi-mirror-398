"""
:filename: whakerkit.connection.tests.test_base_authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The test of the BaseAuthentication class

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

from whakerkit.connection.base_authentication import BaseAuthentication

# ---------------------------------------------------------------------------


class TestBaseAuthentication(unittest.TestCase):

    def test_instantiation(self):
        """Test BaseAuthentication init."""
        result = BaseAuthentication.name()
        self.assertEqual(result, 'base')

        # init without argument
        auth = BaseAuthentication()
        self.assertTrue(auth._available)
        self.assertEqual(auth.name(), "base")
        self.assertIsNone(auth._BaseAuthentication__method_id)

        # init with valid kwarg method_id
        auth_method_id = "example_id"
        auth = BaseAuthentication(method_id=auth_method_id)
        self.assertEqual(auth._BaseAuthentication__method_id, auth_method_id)

        # init with invalid kwarg
        with self.assertRaises(TypeError):
            auth_method_id = 123
            auth = BaseAuthentication(method_id=auth_method_id)

        # init with ignored kwarg
        auth = BaseAuthentication(some_kwarg="some")
        self.assertIsNone(auth._BaseAuthentication__method_id)

    # -----------------------------------------------------------------------

    def test_get_available(self):
        """Test BaseAuthentication get_available."""
        auth = BaseAuthentication()
        result = auth.get_available()
        self.assertTrue(result)
        result = auth.available
        self.assertTrue(result)

    # -----------------------------------------------------------------------

    def test_get_default_name(self):
        """Test BaseAuthentication _get_default_name."""
        # with valid arg
        auth = BaseAuthentication()
        result = auth._get_default_name(BaseAuthentication)
        self.assertEqual(result, "base")

        # with invalid arg
        with self.assertRaises(TypeError):
            auth._get_default_name(auth)

        # subclass, but forget to change name
        class UnexpectedFormatAuthentication(BaseAuthentication):
            def __init__(self):
                super().__init__()
        authentication = UnexpectedFormatAuthentication()
        result = BaseAuthentication._get_default_name(UnexpectedFormatAuthentication)
        self.assertEqual(result, "unexpectedformat")
        # because 'name()' is not overridden, the name is still 'base'
        self.assertEqual(authentication.name(), "base")

        # properly subclass
        class UnexpectedFormatAuthentication(BaseAuthentication):
            def __init__(self):
                super().__init__()
            @staticmethod
            def name():
                return 'custom_name'
        authentication = UnexpectedFormatAuthentication()
        self.assertEqual(authentication.name(), "custom_name")

    # -----------------------------------------------------------------------

    def test_name(self):
        """Test BaseAuthentication name."""
        auth_method_name = "base"
        auth = BaseAuthentication()
        self.assertEqual(auth.name(), auth_method_name)

    # -----------------------------------------------------------------------

    def test_get_method_id(self):
        """Test BaseAuthentication get_method_id."""
        auth_method_id = "example_id"
        auth = BaseAuthentication(method_id=auth_method_id)
        self.assertEqual(auth.get_method_id(), auth_method_id)
        self.assertEqual(auth.method_id, auth_method_id)

    # -----------------------------------------------------------------------

    def test_authenticate(self):
        """Test BaseAuthentication authenticate."""
        auth = BaseAuthentication()
        with self.assertRaises(NotImplementedError):
            auth.authenticate()

    # -----------------------------------------------------------------------

    def test_get_args(self):
        """Test BaseAuthentication get_args."""
        auth = BaseAuthentication()
        with self.assertRaises(NotImplementedError):
            auth.get_args()
