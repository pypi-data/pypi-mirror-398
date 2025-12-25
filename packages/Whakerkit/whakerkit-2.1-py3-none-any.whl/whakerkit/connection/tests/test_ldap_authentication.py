"""
:filename: whakerkit.connection.tests.test_authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The test of the LdapAuthentication class.

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
from unittest.mock import Mock
from unittest.mock import patch
try:
    from ldap3 import Server
    LDAP = True
except ImportError:
    LDAP = False

from whakerkit.connection.ldap_authentication import LdapAuthentication

# ---------------------------------------------------------------------------


class LdapAuthenticationTest(unittest.TestCase):

    def setUp(self):
        self.domain = 'example.com'

    # -----------------------------------------------------------------------
    def test_instantiation_ldap_unavailable(self):
        """Test LdapAuthentication init."""
        if LDAP is False:
            auth = LdapAuthentication(self.domain)
            self.assertEqual(auth.name(), "ldap")
            self.assertFalse(auth._available)

    # -----------------------------------------------------------------------

    def test_instantiation_ldap_available(self):
        """Test LdapAuthentication init."""
        if LDAP is False:
            return
        # init with valid domain
        auth = LdapAuthentication(self.domain)
        self.assertEqual(auth.name(), "ldap")
        self.assertTrue(auth._available)
        self.assertIsNone(auth.method_id)
        self.assertEqual(auth._LdapAuthentication__domain, self.domain)
        server = Server(host=self.domain, port=389, use_ssl=False,
                        allowed_referral_hosts=[('*', True)], get_info='ALL',
                        mode='IP_V6_PREFERRED')
        self.assertEqual(repr(auth._LdapAuthentication__server), repr(server))

        # init with invalid domain
        with self.assertRaises(TypeError):
            domain = 123
            LdapAuthentication(domain)

        # init with valid domain, and valid id
        ldap_id = "ldap_id"
        auth = LdapAuthentication(self.domain, method_id=ldap_id)
        self.assertEqual(auth.name(), "ldap")
        self.assertEqual(auth.method_id, "ldap_id")

    # -----------------------------------------------------------------------

    def test_get_method_name(self):
        """Test BaseAuthentication get_method_name."""
        auth = LdapAuthentication(self.domain)
        auth_method_name = auth._get_default_name(LdapAuthentication)
        self.assertEqual(auth.name(), auth_method_name)

    # -----------------------------------------------------------------------

    def test_get_args(self):
        """Test LdapAuthentication get_args."""
        if LDAP is True:
            auth = LdapAuthentication(self.domain)
            result = auth.get_args()
            self.assertEqual(result, [self.domain])
            self.assertIsInstance(result, list)
            # extra argument
            with self.assertRaises(TypeError):
                auth.get_args("extra_argument")
        else:
            auth = LdapAuthentication(self.domain)
            result = auth.get_args()
            self.assertEqual(result, [])

    # -----------------------------------------------------------------------

    def test_test_ldap_connection(self):
        """Test LdapAuthentication test_ldap_connection."""
        if LDAP is True:
            # Mock the Connection class
            mock_connection = Mock()
            mock_connection.bind.return_value = True
            patch('ldap3.Connection', return_value=mock_connection)

            # Test bind
            result = LdapAuthentication._LdapAuthentication__test_ldap_connection(mock_connection)
            self.assertIsNone(result)
            mock_connection.bind.assert_called_once()

    # -----------------------------------------------------------------------

    def test_create_connection(self):
        """Test LdapAuthentication create_connection."""
        if LDAP is True:
            auth = LdapAuthentication(self.domain)

            # Mock the Connection class
            mock_connection = Mock()
            mock_connection.bind.return_value = True
            patch('ldap3.Connection', return_value=mock_connection)

            # auth._LdapAuthentication__create_ldap_connection("username", "password")
            # mock_connection.bind.assert_called_once()

            # result = auth.authenticate("user@1.com", "pass&éàç#1!,")
            # self.assertTrue(result)

    # -----------------------------------------------------------------------
    # overloads
    # -----------------------------------------------------------------------

    def test_str(self):
        """Test LdapAuthentication __str__."""
        auth = LdapAuthentication(self.domain)
        if LDAP is True:
            auth._LdapAuthentication__server = None
            result = auth.__str__()
            self.assertEqual(result, "{:s}(domain: {:s}, id={})"
                                     "".format(auth.__class__.__name__, self.domain, auth.method_id))

            server = Server(host=self.domain, port=389, use_ssl=False,
                            allowed_referral_hosts=[('*', True)], get_info='ALL',
                            mode='IP_V6_PREFERRED')
            auth = LdapAuthentication(self.domain)
            result = auth.__str__()
            self.assertEqual(result, "{:s}(domain: {:s}, id={})"
                                     "".format(auth.__class__.__name__, self.domain, auth.method_id))
        else:
            result = auth.__str__()
            self.assertEqual(result, "{:s} unavailable".format(auth.__class__.__name__))

    # -----------------------------------------------------------------------

    def test_repr(self):
        """Test LdapAuthentication __repr__."""
        auth = LdapAuthentication(self.domain)
        if LDAP is True:
            # without id
            self.assertEqual(repr(auth),
                             "{:s}(name: '{:s}', id: 'None', domain: '{:s}')"
                             "".format(auth.__class__.__name__, auth.name(), self.domain))

            # with id
            ldap_id = "ldap-id"
            auth = LdapAuthentication(self.domain, method_id=ldap_id)
            self.assertEqual(repr(auth),
                             "{:s}(name: '{:s}', id: '{:s}', domain: '{:s}')"
                             "".format(auth.__class__.__name__, auth.name(), ldap_id, self.domain))
        else:
            auth = LdapAuthentication(self.domain)
            self.assertEqual(repr(auth), "{:s} unavailable".format(auth.__class__.__name__))
