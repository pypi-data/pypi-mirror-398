"""
:filename: whakerkit.connection.connection.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Connection manager to deal with authentication methods.

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

from .authentication import Authentication

# ---------------------------------------------------------------------------


class Connection:
    """Manage multiple authentication methods.

    This class supports dynamically adding and using different authentication
    methods. The Connection class is used to manage the authentication methods
    and to authenticate a user.

    :example:
    >>> connection = Connection()
    >>> # Enable a method without id
    >>> connection.enable_method("ldap", True, "test.dom")
    >>> # Enable a method with id
    >>> connection.enable_method("ldap", True, "cert", id="example_id_ldap")
    >>> # Authenticate a user using the enabled methods
    >>> connection.connect("ldap", "test", "test")
    >>> # Disable a method
    >>> connection.enable_method("ldap", True, "cert", id="example_id_ldap")
    >>> # Get the list of enabled methods
    >>> connection.get_methods_ids()
    ['ldap_id', 'certificate_id']
    >>> # Get the authentication method by its name
    >>> connection.get_authentication_method_by_name("ldap")

    """

    def __init__(self):
        """Create a Connection instance."""
        self.__enabled_methods = []
        self.__auth_methods = Authentication()

    # -----------------------------------------------------------------------

    @staticmethod
    def check_string(s: str) -> None:
        """Raise TypeError if the given parameter is not a string.

        :param s: (str) A string to be checked.
        :raises: TypeError: the given parameter is not a string.

        """
        if isinstance(s, str) is False:
            raise TypeError("Expected a string. Got {} instead.".format(type(s)))

    # -----------------------------------------------------------------------

    @staticmethod
    def check_bool(b: bool) -> None:
        """Raise TypeError if the given parameter is not a bool.

        :param b: (bool) A boolean to be checked.
        :raises: TypeError: the given parameter is not a boolean.

        """
        if isinstance(b, bool) is False:
            raise TypeError("Expected a bool. Got {} instead.".format(type(b)))

    # -----------------------------------------------------------------------

    def get_methods_names(self) -> list:
        """Get the list of enabled authentication method names.

        :return: (list) the list of enabled authentication method names

        """
        return list(set([m.name() for m in self.__enabled_methods]))

    # -----------------------------------------------------------------------

    def get_methods_ids(self) -> list:
        """Get the list of enabled authentication methods.

        :return: (list) the list of enabled authentication method identifiers

        """
        return [m.get_method_id() for m in self.__enabled_methods if m.get_method_id() is not None]

    # -----------------------------------------------------------------------

    def get_authentication_method_by_name(self, name: str) -> object:
        """Get an authentication method by its name.

        :param name: (str) the name of the method
        :raises: KeyError: the method is not found
        :raises: TypeError: the name is not a string
        :return: (obj) the authentication class

        """
        Connection.check_string(name)
        for method in self.__enabled_methods:
            if method.name() == name:
                return method

        raise KeyError(f"No authentication method found with name '{name}'.")

    # -----------------------------------------------------------------------

    def get_authentication_method_by_id(self, auth_id: str) -> object:
        """Get the authentication method by its id.

        :param auth_id: (str) the id of the method
        :raises: KeyError: the method is not found
        :raises: TypeError: the given id is not a string
        :return: (obj) the authentication class

        """
        Connection.check_string(auth_id)
        for method in self.__enabled_methods:
            if method.get_method_id() == auth_id:
                return method

        raise KeyError(f"Connection.get_authentication_method_by_id: "
                       f"No authentication method found with id '{auth_id}'.")

    # -----------------------------------------------------------------------

    def enable_method(self, name: str, value: bool, *args, **kwargs) -> bool:
        """Enable or disable an authentication method.

        It is allowed to enable as many different authentication methods as possible.
        However, it is not allowed to enable the same method multiple times, except
        if the authentication instances have different identifiers.

        :param name: (str) the name of the method to add or remove
        :param value: (bool) if the method is enabled or not
        :param args: (list) the arguments of the method
        :param kwargs: (dict) the keywords arguments of the method
        :raises: TypeError: the method is not a string
        :raises: TypeError: the value is not a boolean
        :raises: KeyError: unknown method name
        :return: (bool) if enabled or disabled

        """
        # Check if the method is a string and the value is a boolean
        Connection.check_string(name)
        Connection.check_bool(value)

        # Either get authentication identifier from kwargs or set to None
        method_id = None
        if "method_id" in kwargs:
            method_id = kwargs["method_id"]
            kwargs.pop('method_id')

        # Enable or disable the given method
        if value is True:
            return self.__enable(name, method_id, *args, **kwargs)
        else:
            return self.__disable(name, method_id)

    # -----------------------------------------------------------------------

    def __enable(self, name: str, method_id: str | None, *args, **kwargs) -> bool:
        """Enable an authentication method.
        
        :param name: (str) the name of the method to add
        :param method_id: (str | None) Method identifier
        :param args: (dict) the arguments of the credentials depends on the method
        :param kwargs: (dict) the arguments of the credentials depends on the method
        :raises: TypeError: the method is not a string
        :raises: TypeError: the value is not a boolean
        :raises: KeyError: unknown method name
        :return: (bool) whether the authentication method has been enabled or not

        """
        if method_id is not None:
            # Can't enable an authentication method with the same identifier twice.
            for m in self.__enabled_methods:
                # Check if there is a method with the same id
                if m.get_method_id() == method_id:
                    logging.info(f"Authentication method with identifier '{method_id}' is already enabled.")
                    return False
        else:
            # Can't enable an authentication method with the same name twice,
            # except if the method has an identifier.
            for m in self.__enabled_methods:
                # Check if there is a method with the same name and with no id
                if m.name() == name and m.get_method_id() is None:
                    logging.info(f"Authentication method with name '{name}' is already enabled. ")
                    return False

        # Create the instance of the method -- or raise an exception
        auth = self.__auth_methods.get_auth_class(name)(*args, method_id=method_id, **kwargs)
        if auth.available is True:
            self.__enabled_methods.append(auth)

        return auth.available

    # -----------------------------------------------------------------------

    def __disable(self, name: str, method_id: str | None) -> bool:
        """Disable an authentication method from its name or identifier.

        :param name: (str) the name of the method to remove
        :param method_id: (str | None) Method identifier
        :raises: TypeError: the method is not a string
        :raises: TypeError: the value is not a boolean
        :raises: KeyError: unknown method name
        :return: (bool) whether the authentication method has been enabled or not

        """
        for auth in self.__enabled_methods:
            if auth.name() == name:
                if method_id is None or (method_id is not None and auth.get_method_id() == method_id):
                    # No id: Compare only the name.
                    # With an id: Compare both the name and the id.
                    self.__enabled_methods.remove(auth)
                    return True

        logging.info(f"None of the enabled authentication methods are matching "
                     f"both name '{name}' and id '{method_id}'.")
        return False

    # -----------------------------------------------------------------------

    def connect(self, name: str, *args, **kwargs) -> tuple[bool, str]:
        """Authenticate a user using the specified method.

        :param name: (str) the method to use for authentication
        :param args: the credentials required by the authentication method
        :param kwargs: the id of the method if it is needed
        :raises: TypeError: the name is not a string
        :raises: TypeError: the args are not a tuple
        :raises: ValueError: the method is not configured
        :return: (bool) Authentication success or failure

        :example:
        >>> connection = Connection()
        >>> connection.enable_method(JwtAuthentication.name(), True, "secret_key", method_id="example_id")
        >>> connection.get_authentication_method_by_id("example_id").generate_token("test")
        >>> connection.connect(JwtAuthentication.name(), "test", method_id="example_id")

        TODO: re-write this method to turn it into something humanly understandable, and test it.

        """
        method_id = None
        if "method_id" in kwargs:
            method_id = kwargs["method_id"]
        Connection.check_string(name)
        if isinstance(args, tuple) is False:
            raise TypeError(
                f"Connection.connect: Expected a tuple for 'credentials', but received '{type(args).__name__}'.")
        for credential in args:
            if isinstance(credential, str) is False:
                raise TypeError(f"Connection.connect: "
                                f"Expected a tuple of string for 'credentials', "
                                f"but received a '{type(credential).__name__}'. in the tuple.")
        for auth in self.__enabled_methods:
            if auth.name() == name and (method_id is None or auth.get_method_id() == method_id):
                return auth.authenticate(*args)
        raise ValueError(f"Connection.connect: "
                         f"Cannot authenticate using '{name}'. The method is not available or not configured.")

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        """Return the informal string representation of the class.

        :return: (str) The informal string representation

        """
        return f"Connection({self.__enabled_methods})"

    # -----------------------------------------------------------------------

    def __repr__(self):
        """Return the official string representation of the class.

        :return: (str) The official string representation

        """
        enabled_methods_repr = ", ".join([
            "(name: '{}', id: '{}', args: {})".format(method.name(), method.get_method_id(), method.get_args())
            for method in self.__enabled_methods
        ])
        return "Connection({})".format(enabled_methods_repr)
