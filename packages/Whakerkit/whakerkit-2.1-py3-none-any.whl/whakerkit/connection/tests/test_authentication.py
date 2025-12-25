"""
:filename: whakerkit.connection.tests.test_authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The test of the Authentication class.

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

from whakerkit.connection.authentication import Authentication

# ---------------------------------------------------------------------------


class TestAuthentication(unittest.TestCase):

    def test_instantiation(self):
        conn_methods = Authentication()
        self.assertIn("ldap", conn_methods._Authentication__methods)
        self.assertIn("jwt", conn_methods._Authentication__methods)

    # -----------------------------------------------------------------------

    def test_get_method_names(self):
        """Test Authentication get_method_names()."""
        conn_methods = Authentication()
        names = conn_methods.get_method_names()
        self.assertIn("jwt", names)
        self.assertIn("ldap", names)

    # -----------------------------------------------------------------------

    def test_available_method_names(self):
        """Test Authentication get_available_method_names()."""
        conn_methods = Authentication()
        names = conn_methods.get_method_names()
        is_ok = list()
        for name in names:
            auth_class = conn_methods.get_auth_class(name)
            if auth_class.available is True:
                is_ok.append(name)
        self.assertEqual(len(is_ok), len(conn_methods.get_available_method_names()))

    # -----------------------------------------------------------------------

    def test_get_auth_class(self):
        """Test Authentication get_auth_class()."""
        conn_methods = Authentication()

        # with a valid name
        auth_class = conn_methods.get_auth_class("ldap")
        self.assertTrue(auth_class.name(), "ldap")
        auth_class = conn_methods.get_auth_class("jwt")
        self.assertTrue(auth_class.name(), "jwt")

        # with an invalid name
        with self.assertRaises(KeyError):
            conn_methods.get_auth_class("unknown")
        with self.assertRaises(KeyError):
            conn_methods.get_auth_class(None)
        with self.assertRaises(KeyError):
            conn_methods.get_auth_class(123)
        with self.assertRaises(KeyError):
            conn_methods.get_auth_class("")
