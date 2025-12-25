"""
:filename: whakerkit.connection.ldap_authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Authentication based on LDAP protocol.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io

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
import logging
try:
    from ldap3 import Server
    from ldap3 import Connection
    from ldap3 import NTLM
    from ldap3 import ALL

    LDAP = True
except ImportError:
    LDAP = False


    class Connection:
        pass


    class Server:
        pass

from .base_authentication import BaseAuthentication

# ---------------------------------------------------------------------------


class LdapAuthentication(BaseAuthentication):
    """Lightweight Directory Access Protocol authentication method.

    The Lightweight Directory Access Protocol (LDAP) is an open, vendor-neutral,
    industry standard application protocol for accessing and maintaining
    distributed directory information services over an Internet Protocol (IP)
    network.

    A common use of LDAP is to provide a central place to store usernames 
    and passwords. This allows many different applications and services to
    connect to the LDAP server to validate users.

    """

    def __init__(self, domain: str, **kwargs):
        """Create an LdapAuthentication instance.

        :param domain: (str) the domain of the server
        :raises: TypeError: given ``domain`` is not a string

        """
        super(LdapAuthentication, self).__init__(**kwargs)

        self._available = LDAP
        if self._available is False:
            self.__domain = None
            self.__server = None
            self.__connexion = None
            logging.warning("LdapAuthentication was not initialized: "
                            "requirement to 'ldap3' module is not satisfied.")
        else:
            if isinstance(domain, str) is False:
                raise TypeError("LdapAuthentication 'domain' must be a string. "
                                "Got {} instead.".format(type(domain)))
            self.__domain = domain
            self.__server = Server(self.__domain, get_info=ALL)

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Override. Return the name of the authentication method.

        :return: (str) The name of the authentication method.

        """
        return BaseAuthentication._get_default_name(LdapAuthentication)

    # -----------------------------------------------------------------------

    def get_args(self) -> list:
        """Override. Return the domain of the LDAP authentication.

        :return: (str) The LDAP domain or an empty list if LDAP is not available

        """
        if self._available is True:
            return [self.__domain]
        return []

    # -----------------------------------------------------------------------

    def authenticate(self, username: str, password: str) -> tuple[bool, str]:
        """Authenticate a user from its login and password.

        :param username: (str) the username of the user
        :param password: (str) the password of the user
        :return: (bool) User is successfully authenticated
        :raises: TypeError: given ``username`` or ``password`` are not strings

        """
        if self._available is False:
            return False, "LdapAuthentication unavailable"

        if isinstance(username, str) is False:
            raise TypeError("LdapAuthentication 'username' must be a string. Got {} instead."
                            "".format(type(username).__name__))
        if isinstance(password, str) is False:
            raise TypeError("LdapAuthentication 'password' must be a string. Got {} instead."
                            "".format(type(password)))

        try:
            self.__connexion = self.__create_ldap_connection(username, password)
            return True, "User successfully authenticated"
        except Exception as e:
            logging.error("Connection to server '{:s}' in domain '{:s}' failed due to "
                          "the following error: {:s}".format(repr(self.__server), self.__domain, str(e)))
            return False, f"User not authenticated due to the following error: {e}"

    # -----------------------------------------------------------------------

    def close(self):
        """Close the connection."""
        if self.__connexion is not None:
            self.__connexion.unbind()
            self.__connexion = None

    # -----------------------------------------------------------------------

    def get_full_name(self, username: str) -> str:
        """Return the full name of a user.

        :param username: (str) the username of the user
        :return: (str) the full name of the user

        """
        if self.__connexion is not None:
            dn_base = ','.join([f'DC={elem}' for elem in self.__domain.split(".")])
            search_filter = '(sAMAccountName=' + username + ')'
            self.__connexion.search(dn_base, search_filter, attributes="displayName")
            for entree in self.__connexion.entries:
                return str(entree.displayName)
        return "Anonymous"

    # -----------------------------------------------------------------------

    def __create_ldap_connection(self, username: str, password: str) -> Connection:
        """Establish a connection to the LDAP server.

        :param username: (str) the username of the user
        :param password: (str) the password of the user
        :return: (bool) User is successfully authenticated
        :raises: Exception: No connection establishment is possible

        """
        if self._available is True:
            c = Connection(self.__server, user=f'{self.__domain}\\{username}',
                           password=password, authentication=NTLM)
            LdapAuthentication.__test_ldap_connection(c)
            return c
        else:
            raise ConnectionError("LdapAuthentication unavailable")

    # -----------------------------------------------------------------------

    @staticmethod
    def __test_ldap_connection(c: Connection) -> None:
        """Test the connection to the LDAP server."""
        if not c.bind():
            # ldap3 documentation does not indicate what is the returned value
            # of "bind()" (True/False?, None?, a numeric value???).
            raise ConnectionError(str(c.result))

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        """Return the string representation of the class.

        :return: (str) A string representation of the LdapAuthentication
        
        """
        if self._available is False:
            return "{:s} unavailable".format(self.__class__.__name__)
        return ("{:s}(domain: {:s}, id={})"
                "").format(self.__class__.__name__, self.__domain, self.method_id)

    # -----------------------------------------------------------------------

    def __repr__(self):
        """Return the official string representation of the class.

        :return: (str) A string representation of the LdapAuthentication

        """
        if self._available is False:
            return "{:s} unavailable".format(self.__class__.__name__)
        return "{:s}({:s})".format(
            self.__class__.__name__,
            ", ".join(["name: '{:s}'".format(self.name()),
                       "id: '{:s}'".format(str(self.method_id)),
                       "domain: '{:s}'".format(self.__domain)])
        )
