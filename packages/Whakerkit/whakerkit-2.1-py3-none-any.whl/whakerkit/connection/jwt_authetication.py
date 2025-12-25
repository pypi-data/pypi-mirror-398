"""
:filename: whakerkit.connection.jwt_token.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Authentication based on JWT protocol.

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
from datetime import datetime
from datetime import timedelta
from datetime import timezone
try:
    import jwt
    JWT = True
except ImportError:
    JWT = False

from .base_authentication import BaseAuthentication

# ---------------------------------------------------------------------------


class JwtAuthentication(BaseAuthentication):
    """JSON Web Tokens authentication method.

    JSON Web Tokens are an open, industry standard RFC 7519 method for
    representing claims securely between two parties.

    JwtAuthentication allows to decode, verify and generate JWT.

    """

    def __init__(self, secret_key: str, **kwargs):
        """Create a JwtAuthentication instance.

        :param secret_key: (str) The secret key

        """
        super(JwtAuthentication, self).__init__(**kwargs)

        self._available = JWT
        if self._available is False:
            logging.warning("JwtAuthentication was not initialized: requirement to 'jwt' module is not satisfied.")
        else:
            if isinstance(secret_key, str) is False:
                raise TypeError("JwtAuthentication secret key must be a 'str'. "
                                f"Got '{type(secret_key).__name__}' instead.")
            self.__secret_key = secret_key

    # -----------------------------------------------------------------------

    @staticmethod
    def name() -> str:
        """Override. Return the name of the authentication method.

        :return: (str) The name of the authentication method.

        """
        return BaseAuthentication._get_default_name(JwtAuthentication)

    # -----------------------------------------------------------------------

    def get_args(self) -> list:
        """Return the secret key of the JWT.

        :return: (list) The secret key or an empty list if JWT is not available

        """
        if self._available is True:
            return [self.__secret_key]
        return []

    # -----------------------------------------------------------------------

    def authenticate(self, token: str) -> tuple[bool, str]:
        """Verify a token.

        Verify by decoding the given token, and checking both its validity
        and expiration date.

        :param token: (str) The token to verify
        :return: (bool) True if the token is valid, False otherwise)

        """
        if self._available is False:
            return False, "JwtAuthentication unavailable"

        if isinstance(token, str) is False:
            raise TypeError("JwtAuthentication.authenticate: Token must be a 'string'. "
                            f"Got a '{type(token).__name__}' instead.")
        if len(token) == 0:
            return False, "Token is empty"

        try:
            return True, self.decode_token(token)
        except KeyError:
            return False, "Token is invalid"

    # -----------------------------------------------------------------------

    def generate_token(self, entry: str, validity: int = 30) -> str | None:
        """Generate a JWT token from the given parameter.

        :param entry: (str) The string to encode in the token
        :param validity: (int) The amount of time in seconds that the token should expire
        :return: (str | None) A coded token or None if JWT is not available
        :raises: TypeError: if the entry is invalid

        """
        if self._available is False:
            return None
        if isinstance(entry, str) is False:
            raise TypeError("Entry to generate a token must be a string."
                            f"Got {type(entry).__name__} instead.")
        if isinstance(validity, int) is False:
            logging.error("JwtAuthentication.generate_token: validity must be a 'int'. "
                          "Set to 30 minutes.")
            validity = 30
        payload = {
            'exp': datetime.now(tz=timezone.utc) + timedelta(minutes=validity),
            'iat': datetime.now(tz=timezone.utc),
            'sub': entry
        }
        return jwt.encode(payload, self.__secret_key, algorithm='HS256')

    # -----------------------------------------------------------------------

    def decode_token(self, token: str) -> str | None:
        """Decode a JWT token.

        :param token: (str) the token to be decoded
        :return: (str | None) the decoded token or None if JWT is not available
        :raises: KeyError: if the token is invalid
        :raises: KeyError: if the token is expired

        """
        if self._available is False:
            return None
        if isinstance(token, str) is False:
            raise TypeError("Token to be decoded must be a string."
                            f"Got {type(token).__name__} instead.")
        try:
            payload = jwt.decode(token, self.__secret_key, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise KeyError("Token is expired")
        except jwt.InvalidTokenError:
            raise KeyError("Token is invalid")

    # -----------------------------------------------------------------------

    def __str__(self):
        """Return a string representation of the class.

        :return: (str) A string representation of the JwtAuthentication

        """
        if self._available is False:
            return "{:s} unavailable".format(self.__class__.__name__)
        return ("{:s}(secret key: '{:s}', id: '{}')"
                "").format(self.__class__.__name__, self.__secret_key, self.method_id)

    # -----------------------------------------------------------------------

    def __repr__(self):
        """Return the official string representation of the class.

        :return: (str) The official string representation of the JwtAuthentication

        """
        if self._available is False:
            return "{:s} unavailable".format(self.__class__.__name__)
        return "{:s}({:s})".format(
            self.__class__.__name__,
            ", ".join(["name: '{}'".format(self.name()),
                       "id: '{}'".format(self.method_id),
                       "secret key: '{}'".format(self.__secret_key)])
        )
