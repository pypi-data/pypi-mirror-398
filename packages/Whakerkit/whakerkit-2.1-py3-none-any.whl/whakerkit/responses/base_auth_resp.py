# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.responses.base_auth_resp.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Dynamic bakery system for the authenticated users

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

"""

from __future__ import annotations
import logging

from whakerpy.htmlmaker import HTMLNode

import whakerkit
from whakerkit import get_msg
from ..connection import Connection
from ..connection import JwtAuthentication
from ..connection import LdapAuthentication

from .base import get_base_response_class  # WhakerKitResponse or Custom

# ---------------------------------------------------------------------------


MSG_BASE_SUCCESS = "Operation successful"
MSG_AUTHENTICATED = "User authenticated"

MSG_BASE_FAILED = "An error occurred: "
MSG_NOT_AUTHENTICATED = "User not authenticated: "
MSG_NON_AUTHORIZED = "User not authorized: "
MSG_LOGIN_FAILED = "Incorrect username or password."

MSG_LOGOUT_SUCCESS = "Logout successful"
MSG_LOGOUT_FAILED = "Logout failed"

MSG_MISSING_JWT = ("PyJWT must be installed on the server to enable login. "
                   "Contact the website administrator.")

# ---------------------------------------------------------------------------

HEADER_SCRIPT = """
    import { AuthenticationManager } from './whakerkit/statics/js/authenticate.js';

    const authManager = new AuthenticationManager("%d");
    document.addEventListener('DOMContentLoaded', () => {
        authManager.handleAuthenticationOnLoad();
    });
    window.authManager = authManager;
""" % logging.getLogger().getEffectiveLevel()

# ---------------------------------------------------------------------------


class WhakerkitAuthResponse(get_base_response_class()):
    """Create a response system for any dynamic pages requiring an authentication.

    """

    def __init__(self, name: str | None = None, tree=None, title: str = whakerkit.sg.name):
        """Create a HTTPD Response instance with a default response.

        :param name: (str) Filename of the body main content.

        """
        # Inheritance with a given dynamic HTMLTree.
        super(WhakerkitAuthResponse, self).__init__(name, tree, title)

        # Authentication
        self._connection = Connection()
        self._connection.enable_method(
            JwtAuthentication.name(), True, whakerkit.sg.secret_key)
        self._connection.enable_method(
            LdapAuthentication.name(), True, whakerkit.sg.domain)

        # Who's authenticated?
        self._is_authenticated = False
        self._author = ""

    # -----------------------------------------------------------------------

    def create(self):
        """Create the deposit page.

        """
        get_base_response_class().create(self)

        css_type = "text/css"
        self._htree.head.link(rel="stylesheet", href=whakerkit.sg.whakerexa + "css/dialog.css", link_type=css_type)

        # JS to authenticate a user
        self._htree.head.script(src=whakerkit.sg.path + "statics/js/authenticate.js", script_type="module")
        auth_script = HTMLNode(self._htree.head.identifier, None, "script", value=HEADER_SCRIPT)
        auth_script.add_attribute("type", "module")
        self._htree.head.append_child(auth_script)

    # -----------------------------------------------------------------------

    def _process_events(self, events: dict, **kwargs) -> bool:
        """Process the given events coming from the POST of any form.

        :param events (dict): key=event_name, value=event_value
        :return: (bool) True if the whole page must be re-created.

        """
        logging.debug(f"WhakerkitAuthResponse._process_events: {events.keys()}.")
        self._status.code = 200

        event_name = events.get("event_name", "")
        if event_name in ("login", "logout"):
            if event_name == "login":
                # Login with username and password
                self.login(
                    events.get("username", ""),
                    events.get("password", "")
                )
            else:
                self.logout()
            return True

        # No processed event: no login/logout action performed
        return False

    # -----------------------------------------------------------------------

    def authenticate(self, token: str):
        """Authenticate a user with JWT from the given token.

        Fix status code to 401 if authentication failed.

        :param token: (str) the token string

        """
        try:
            self._is_authenticated, msg = self._connection.connect(JwtAuthentication.name(), token)
            if self._is_authenticated is True:
                self._author = msg
                self._data = {"token": token}
                logging.debug(" ... Token is validated.")
            else:
                self._data = {"error": get_msg(MSG_NOT_AUTHENTICATED) + msg}
                logging.error("User not authenticated: JWT authentication failed.")
                self._status.code = 401  # Unauthorized
        except Exception as e:
            logging.error(e)
            self._data = {"error": get_msg(MSG_BASE_FAILED) + str(e)}
            logging.error(f"JWT unexpected authentication error: {e}")
            self.status.code = 401

    # -----------------------------------------------------------------------

    def login(self, username: str, password: str):
        """Authenticate a user with LDAP from the given username and password.

        Fix status code to 401 if login failed.

        :param username: (str) Username in LDAP
        :param password: (str) Password in LDAP

        """
        logging.info(f"Login attempt by username='{username}'")
        self._data = {"error": get_msg(MSG_LOGIN_FAILED)}

        # Both a username and a password are fixed.
        if len(username)*len(password) > 0:

            # Connect username/password to LDAP server.
            if logging.getLogger().getEffectiveLevel() > 1:
                self._is_authenticated, msg = self._connection.connect(LdapAuthentication.name(), username, password)
            else:
                self._is_authenticated = True

            if self._is_authenticated is True:
                if logging.getLogger().getEffectiveLevel() > 1:
                    # Authenticate with LDAP.
                    ldap_connection = self._connection.get_authentication_method_by_name("ldap")
                    # Get full name and close the connection.
                    self._author = ldap_connection.get_full_name(username)
                    ldap_connection.close()
                else:
                    self._author = "Anne Ony-misée"

                # Generate a personal token, valid for a few hours.
                try:
                    jwt = self._connection.get_authentication_method_by_name(JwtAuthentication.name())
                    token = jwt.generate_token(self._author, whakerkit.sg.jwt_validity)
                    logging.debug(f" ... JWT generated token: {token}")
                    # check token validity
                    self.authenticate(token)
                    logging.info(f" ... login {username} succeeded. {self._author} is authenticated.")
                    return
                except KeyError:
                    # jwt is not installed.
                    self._data = {"error": get_msg(MSG_MISSING_JWT)}
            else:
                self._data = {"error": get_msg(MSG_NOT_AUTHENTICATED) + msg}
        else:
            self._data = {"error": get_msg(MSG_LOGIN_FAILED)}

        logging.info(f"Login failed. '{username}' is not authenticated: {self._data['error']}")
        self.status.code = 401

    # -----------------------------------------------------------------------

    def logout(self):
        """Logout a user from the given events.

        """
        pass
