"""
:filename: whakerkit.connection.base_authentication.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The base class for all authentication backends.

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
import inspect

# ---------------------------------------------------------------------------


class BaseAuthentication:
    """Base class for all authentication back-ends.

    Its purpose is to provide an easy interface to authenticate a user.

    Any authentication method is characterized by two parameters: its name
    and its identifier. The name is specific to each authentication backend.
    but the identifier is specific to each authentication instance.

    """

    def __init__(self, method_id: str | None = None, *args, **kwargs):
        """Initialize the authentication method.

        :param method_id: (str | None) Identifier of the authentication method
        :param args: (dict) Credentials for a subclass of BaseAuthentication.
        :param kwargs: (dict) Keywords for a subclass of BaseAuthentication.
        :raises: TypeError: Invalid given ``method_id``
        
        """
        # Does all requirements satisfied?
        self._available = True

        # Identifier of an instance of the authentication method
        self.__method_id = None
        if method_id is not None:
            if isinstance(method_id, str) is False:
                raise TypeError("BaseAuthentication method_id must be a string. "
                                f"Got '{type(method_id).__name__}' instead.")
            if len(method_id) > 0:
                self.__method_id = method_id

    # -----------------------------------------------------------------------

    def get_available(self) -> bool:
        """Return True if authentication is available."""
        return self._available

    available = property(get_available, None, None)

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Return the name of the authentication method.

        Must be overridden by subclasses.

        :return: (str) The name of the authentication method.

        """
        return BaseAuthentication._get_default_name(BaseAuthentication)

    # -----------------------------------------------------------------------

    def get_method_id(self) -> str | None:
        """Return the id of the authentication method or None.

        :return: (str | None) The id of the method if set, None otherwise.

        """
        return self.__method_id

    method_id = property(get_method_id, None, None)

    # -----------------------------------------------------------------------

    def authenticate(self, *args, **kwargs) -> tuple[bool, str]:
        """The authentication base method, must be overridden.

        Must be overridden by subclasses.

        :param args: (any) the arguments of the credentials depends on the method
        :param kwargs: (dict) the arguments of the credentials depends on the method
        :return: (bool) True if the authentication is successful, False otherwise

        """
        raise NotImplementedError("{:s} does not implement 'authenticate' method.".format(self.__class__.__name__))

    # -----------------------------------------------------------------------

    def get_args(self) -> list:
        """Return the arguments of the authentication method.

        Must be overridden by subclasses.

        :return: (list) The arguments of the method

        """
        raise NotImplementedError("{:s} does not implement 'get_args' method.".format(self.__class__.__name__))

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def _get_default_name(obj: object) -> str:
        """Return a default name for the given authentication method.

        :param obj: (class) The authentication method to use.
        :return: (str) The default name of the authentication method.
        :raises: TypeError: Invalid given parameter.

        """
        if inspect.isclass(obj) is False:
            raise TypeError("Invalid parameter to define a default name. Expected a 'class'.")
        return obj.__name__.replace("Authentication", "").lower()
