"""
:filename: whakerkit.connection.tests.test_jwt_token.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The test of the JwtAuthentication class.

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
try:
    import jwt
    JWT = True
except ImportError:
    JWT = False

from whakerkit.connection.jwt_authetication import JwtAuthentication


class TestJwtAuthentication(unittest.TestCase):

    def setUp(self):
        self.secret_key = "testSecretKey"

    # -----------------------------------------------------------------------

    def test_instantiation_jwt_unavailable(self):
        """Test JwtAuthentication init."""
        if JWT is False:
            auth = JwtAuthentication(self.secret_key)
            self.assertEqual(auth.name(), "jwt")
            self.assertFalse(auth._available)

    # -----------------------------------------------------------------------

    def test_instantiation_jwt_available(self):
        """Test JwtAuthentication init."""
        if JWT is False:
            return
        # init with valid secret_key
        auth = JwtAuthentication(self.secret_key)
        self.assertEqual(auth.name(), "jwt")
        self.assertTrue(auth._available)
        self.assertIsNone(auth.method_id)
        self.assertEqual(auth._JwtAuthentication__secret_key, self.secret_key)

        # init with invalid secret_key
        with self.assertRaises(TypeError):
            JwtAuthentication(123)

        # init with valid secret_key, and valid id
        ldap_id = "jwt_id"
        auth = JwtAuthentication(self.secret_key, method_id=ldap_id)
        self.assertEqual(auth.name(), "jwt")
        self.assertEqual(auth.method_id, "jwt_id")

        # init with valid secret_key, and invalid kwarg
        auth = JwtAuthentication(self.secret_key, some="some", invalid="invalid")
        self.assertEqual(auth.name(), "jwt")
        self.assertTrue(auth._available)
        self.assertIsNone(auth.method_id)
        self.assertEqual(auth._JwtAuthentication__secret_key, self.secret_key)

    # -----------------------------------------------------------------------

    def test_get_method_name(self):
        """Test BaseAuthentication get_method_name."""
        auth = JwtAuthentication(self.secret_key)
        auth_method_name = auth._get_default_name(JwtAuthentication)
        self.assertEqual(auth.name(), auth_method_name)

    # -----------------------------------------------------------------------

    def test_generate_token(self):
        auth = JwtAuthentication(self.secret_key)
        entry = "testUser"
        token = auth.generate_token(entry)

        if auth.available is True:
            # with valid entry
            self.assertIsNotNone(token)
            self.assertIsInstance(token, str)
            self.assertNotEqual(token, "")

            # with invalid entry
            with self.assertRaises(TypeError):
                auth.generate_token(123)
        else:
            self.assertIsNone(token)

    # -----------------------------------------------------------------------

    def test_generate_and_decode(self):
        """Test consecutively to generate and decode a token."""
        auth = JwtAuthentication(self.secret_key)
        entry = "testUser"
        token = auth.generate_token(entry)

        if auth.available is True:
            decoded = auth.decode_token(token)
            self.assertEqual(decoded, entry)

            with self.assertRaises(TypeError):
                auth.generate_token(None)
        else:
            self.assertIsNone(token)

    # -----------------------------------------------------------------------

    def test_authenticate(self):
        auth = JwtAuthentication(self.secret_key)
        entry = "testUser"

        if auth.available is True:
            # with a valid token
            token = auth.generate_token(entry)
            result = auth.authenticate(token)[1]
            self.assertTrue(result)

            # with an invalid token
            with self.assertRaises(TypeError):
                auth.authenticate(123)
        else:
            # with a valid token
            token = auth.generate_token(entry)
            result = auth.authenticate(token)[1]
            self.assertFalse(result)

            # with an invalid token
            result = auth.authenticate(123)[1]
            self.assertFalse(result)

    # -----------------------------------------------------------------------
    # overloads
    # -----------------------------------------------------------------------

    def test_str(self):
        """Test JwtAuthentication __str__."""
        auth = JwtAuthentication(self.secret_key)
        if JWT is True:
            auth._LdapAuthentication__server = None
            result = auth.__str__()
            self.assertEqual(result, "{:s}(secret key: '{:s}', id: '{}')"
                                     "".format(auth.__class__.__name__, self.secret_key, auth.method_id))

            auth = JwtAuthentication(self.secret_key)
            result = auth.__str__()
            self.assertEqual(result, "{:s}(secret key: '{:s}', id: '{}')"
                                     "".format(auth.__class__.__name__, self.secret_key, auth.method_id))
        else:
            result = auth.__str__()
            self.assertEqual(result, "{:s} unavailable".format(auth.__class__.__name__))

    # -----------------------------------------------------------------------

    def test_repr(self):
        """Test JwtAuthentication __repr__."""
        auth = JwtAuthentication(self.secret_key)
        if JWT is True:
            # without id
            self.assertEqual(repr(auth),
                             "{:s}(name: '{:s}', id: 'None', secret key: '{:s}')"
                             "".format(auth.__class__.__name__, auth.name(), self.secret_key))

            # with id
            ldap_id = "ldap-id"
            auth = JwtAuthentication(self.secret_key, method_id=ldap_id)
            self.assertEqual(repr(auth),
                             "{:s}(name: '{:s}', id: '{:s}', secret key: '{:s}')"
                             "".format(auth.__class__.__name__, auth.name(), ldap_id, self.secret_key))
        else:
            auth = JwtAuthentication(self.secret_key)
            self.assertEqual(repr(auth), "{:s} unavailable".format(auth.__class__.__name__))
