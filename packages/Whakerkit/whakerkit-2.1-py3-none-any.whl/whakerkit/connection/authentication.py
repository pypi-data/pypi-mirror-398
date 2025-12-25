"""
:filename: whakerkit.connection.authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The Authentication backends manager.

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

from .ldap_authentication import LdapAuthentication
from .jwt_authetication import JwtAuthentication

# ---------------------------------------------------------------------------


class Authentication:
    """Manage the list of available authentification methods.

    :example:
    >>> # Get the list of available authentication method names
    >>> auth_methods = Authentication()
    >>> auth_methods.get_method_names()
    ["ldap", "certificate", "token", "code"]

    :example:
    >>> # Instantiate an authentication method.
    >>> ldap_auth = auth_methods.get_auth_class(LdapAuthentication().method_name)("here.org")
    >>> jwt_auth = auth_methods.get_auth_class("jwt")("token_secret")

    """

    def __init__(self):
        """Create the list of available authentication methods.

        """
        self.__methods = dict()
        for auth in (
                LdapAuthentication,
                JwtAuthentication
        ):
            name = auth.name()
            self.__methods[name] = auth

    # -----------------------------------------------------------------------

    def get_method_names(self) -> tuple:
        """Return the list of known authentication method names."""
        return tuple(self.__methods.keys())

    # -----------------------------------------------------------------------

    def get_available_method_names(self) -> tuple:
        """Return the list of known and available authentication method names."""
        return tuple([m for m in self.__methods.keys() if self.__methods[m].available is True])

    # -----------------------------------------------------------------------

    def get_auth_class(self, name: str) -> object:
        """Return the authentication class matching the given method name.

        :param name: (str) Name of an authentication method among the known ones.
        :return: (class) The class to be instantiated.
        :raises: (KeyError) Unknown given authentication method name

        """
        method_name = str(name).strip()
        if method_name not in self.__methods:
            raise KeyError("{:s} is not a valid key for authentication. Must be one of: {:s}"
                           "".format(method_name, str(self.__methods.keys())))
        return self.__methods[method_name]

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        return str(tuple(self.__methods.keys()))

    # -----------------------------------------------------------------------

    def __repr__(self):
        return "Authentication({})".format(
            ", ".join(["{:s}: {:s}".format(k, self.__methods[k]) for k in self.__methods]))
