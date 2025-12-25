"""
:filename: whakerkit.connection.tests.test_connection.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The test of the connection module.

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

from whakerkit.connection.connection import Connection
from whakerkit.connection.jwt_authetication import JwtAuthentication
from whakerkit.connection.ldap_authentication import LdapAuthentication

# ---------------------------------------------------------------------------


class TestConnection(unittest.TestCase):

    @staticmethod
    def name():
        return "testname"

    # -----------------------------------------------------------------------

    def test_instantiation(self):
        """Test Connection __init__."""
        connection = Connection()
        self.assertIsInstance(connection, Connection)
        self.assertEqual([], connection._Connection__enabled_methods)
        self.assertIn("ldap", connection._Connection__auth_methods._Authentication__methods)
        self.assertIn("jwt", connection._Connection__auth_methods._Authentication__methods)

    # -----------------------------------------------------------------------

    def test_enable(self):
        """Test Connection enable."""
        # enable without id, with valid arg
        auth = Connection()
        result = auth.enable_method(JwtAuthentication.name(), True, 'secret_key')

        # Whatever 'available' is True or False, result is True.
        # The authentication can be enabled.
        self.assertTrue(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)
        self.assertTrue(JwtAuthentication.name(), names[0])

        # enable without id, with invalid arg
        auth = Connection()
        with self.assertRaises(TypeError):
            auth.enable_method(LdapAuthentication.name(), True, 123)

        with self.assertRaises(TypeError):
            auth.enable_method(JwtAuthentication.name(), True, 123)

        # enable with id, with valid arg
        auth = Connection()
        result = auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="test")
        self.assertTrue(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)
        self.assertTrue(JwtAuthentication.name(), names[0])

        # can't add it twice
        result = auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="test")
        self.assertFalse(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)

        # can add another method with the same name but a different id
        result = auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="another")
        self.assertTrue(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)
        ids = auth.get_methods_ids()
        self.assertEqual(len(ids), 2)

        # can add another method with the same name but without id
        result = auth.enable_method(JwtAuthentication.name(), True, 'secret_key')
        self.assertTrue(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)
        ids = auth.get_methods_ids()
        self.assertEqual(len(ids), 2)

    # -----------------------------------------------------------------------

    def test_disable(self):
        """Test Connection disable."""
        auth = Connection()

        # unconfigured method
        with self.assertRaises(KeyError):
            auth.enable_method(self.name(), True, 'test')

        result = auth.enable_method(JwtAuthentication.name(), False, 'secret_key')
        self.assertFalse(result)

        # disable a valid auth
        auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="test")
        result = auth.enable_method(JwtAuthentication.name(), False)
        self.assertTrue(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 0)

        # attempt to disable an un-existing auth
        auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="test")
        result = auth.enable_method("auth", False)
        self.assertFalse(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)

        result = auth.enable_method(JwtAuthentication.name(), False, method_id="some")
        self.assertFalse(result)
        names = auth.get_methods_names()
        self.assertEqual(len(names), 1)

        # disable with id
        auth.enable_method(JwtAuthentication.name(), True, 'secret_key', method_id="other")
        ids = auth.get_methods_ids()
        self.assertEqual(len(ids), 2)
        auth.enable_method(JwtAuthentication.name(), False, method_id="test")
        ids = auth.get_methods_ids()
        self.assertEqual(len(ids), 1)
        self.assertEqual(ids[0], "other")

    # -----------------------------------------------------------------------

    def test_get_method_names(self):
        """Test Connection get_method_names."""
        # Empty list: no enabled methods
        connection = Connection()
        result = connection.get_methods_names()
        self.assertEqual(result, [])

        # Add methods
        connection = Connection()
        connection.enable_method("ldap", True, "test.dom")

        methods_names = connection.get_methods_names()
        # whatever 'available' is True or False, result is 'ldap'
        result = ["ldap"]
        self.assertEqual(methods_names, result)

        connection.enable_method("jwt", True, "secret_key")
        methods_names = connection.get_methods_names()
        result.append("jwt")
        self.assertEqual(set(methods_names), set(result))

        connection.enable_method("ldap", True, "user", method_id="example_id_oauth")
        methods_names = connection.get_methods_names()
        self.assertEqual(set(methods_names), set(result))

    # -----------------------------------------------------------------------

    def test_get_method_ids(self):
        """Test Connection get_method_ids."""
        # Empty list: no enabled methods
        connection = Connection()
        result = connection.get_methods_ids()
        self.assertEqual(result, [])

        # no method id is given
        connection = Connection()
        connection.enable_method("ldap", True, "test.dom")
        connection.enable_method("jwt", True, "secret_key")
        methods_ids = connection.get_methods_ids()
        self.assertEqual(methods_ids, [])

        # some are given some are not
        connection = Connection()
        connection.enable_method("ldap", True, "test.dom")
        methods_ids = connection.get_methods_ids()
        self.assertEqual(methods_ids, [])

    # -----------------------------------------------------------------------

    def test_str(self):
        connection = Connection()

        # empty
        self.assertEqual(str(connection), "Connection([])")

        # with one auth, no id
        if JwtAuthentication.available is True:
            connection.enable_method(JwtAuthentication.name(), True, secret_key="secret")
            self.assertEqual(str(connection),
                             "Connection([JwtAuthentication(name: 'jwt', id: 'None', secret key: 'secret')])")

        # with and without id
        if LdapAuthentication.available is True:
            connection.enable_method(LdapAuthentication.name(), True, domain="test.domain.com", method_id="dom_id")
            self.assertEqual(str(connection),
                             "Connection([JwtAuthentication(name: 'jwt', id: 'None', secret key: 'secret'), "
                             "LdapAuthentication(name: 'ldap', id: 'dom_id', domain: 'test.domain.com')])")

    # -----------------------------------------------------------------------

    def test_repr(self):
        connection = Connection()

        # empty
        self.assertEqual(repr(connection), "Connection()")

        # with one auth, no id
        if JwtAuthentication.available is True:
            connection.enable_method(JwtAuthentication.name(), True, secret_key="secret")
            self.assertEqual(repr(connection),
                             "Connection((name: 'jwt', id: 'None', args: ['secret']))")

        # with and without id
        if LdapAuthentication.available is True:
            connection.enable_method(LdapAuthentication.name(), True, domain="test.domain.com", method_id="dom_id")
            self.assertEqual(repr(connection),
                             "Connection((name: 'jwt', id: 'None', args: ['secret']), "
                             "(name: 'ldap', id: 'dom_id', args: ['test.domain.com']))")
