import { BaseManager } from '../../../whakerexa/wexa_statics/js/wexa.js'
import { AsideManager } from "./doc_details.js";
/**
_This file is part of WhakerKit: https://whakerkit.sourceforge.io

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

**/

// --------------------------------------------------------------------------

/**
 * AuthenticationManager class handles user authentication with LDAP and JWT tokens.
 *
 * This class provides methods to manage the login process, including verifying tokens,
 * submitting user credentials, and storing tokens. It interacts with the server through a private
 * instance of `RequestManager()` and manages the display of authenticated or anonymous content
 * based on the authentication status.
 *
 * Private Members:
 *  - #requestManager: An instance of the RequestManager class responsible for managing HTTP requests.
 *  - #uri: A string representing the URI used for authentication, extracted from the current URL.
 *
 * Public Methods:
 *  - checkToken(token): Validates a JWT token by sending it to the server and returns the HTTP status.
 *  - storeToken(response): Stores a JWT token in local storage, either from a Blob or string response.
 *  - retrieveToken(): Retrieves the JWT token stored in the local storage.
 *  - submitLogin(username, password): Sends the user's credentials to the server for login and stores the token if successful.
 *  - submitLoginDialog(usernameInputId, passwordInputId): Handles login submission from a dialog and sends credentials via `submitLogin`.
 *  - handleAuthenticationOnLoad(): Manages the authentication state on page load, verifying stored tokens if present.
 *
 * Usage example:
 *  const authManager = new AuthenticationManager();
 *  authManager.submitLogin("username", "password"); // Sends login credentials to the server.
 *  authManager.handleAuthenticationOnLoad(); // Verifies token and updates the page based on the authentication state.
 *
 */
export class AuthenticationManager extends BaseManager {

    // Private
    #logLevel

    constructor(logLevel= 15) {
        // Call the constructor of BaseManager
        super();
        this.#logLevel = logLevel;
    }

    // ----------------------------------------------------------------------
    // JWT
    // ----------------------------------------------------------------------

    /**
     * Check if a JWT token is valid by sending it to the server.
     *
     * @param {string} token - A stored JWT token to be validated.
     * @returns {Promise<number>} - The HTTP status code from the server response.
     *
     */
    async checkToken(token) {
        const response = await this._requestManager.send_post_request({
            "token": token
        }, "application/json", this._uri);
        return this._requestManager.status;
    }

    // ----------------------------------------------------------------------

    /**
     * Store the token in local storage.
     * If the response is a blob, convert it to text before saving.
     *
     * @param {Blob|string} response - The server response containing the token.
     * @returns {Promise<string>} - A promise that resolves with the stored token.
     */
    async storeToken(response) {
        let token = "";

        if (response instanceof Blob) {
            try {
                token = await response.text(); // Await to ensure the Blob is converted to text
                this.setToken(token);           // Now set the token after conversion
            } catch (error) {
                console.error("Error while converting blob to string:", error);
                return ""; // Return an empty string if there was an error
            }
        } else if (response.token !== undefined) {
            token = response.token;
            this.setToken(token);
        } else {
            console.error("Unknown error while storing token");
        }

        console.log("Returned token:", token);
        return token; // Return the token after processing
    }

    // ----------------------------------------------------------------------

    /**
     * Retrieves the authentication token from the browser's local storage.
     *
     * @returns {string|null} The retrieved token from local storage, or `null` if no token is found.
     *
     */
    getToken() {
        return localStorage.getItem("token");
    }

    /**
     * Saves the authentication token to the browser's local storage.
     *
     * @returns {void}
     *
     */
    setToken(token) {
        console.log("Token saved:", token);
        localStorage.setItem("token", token);
    }

    /**
     * Removes the authentication token from the browser's local storage.
     *
     * @returns {void}
     *
     */
    removeToken() {
        console.log("Token removed.");
        localStorage.removeItem("token");
    }

    // ----------------------------------------------------------------------
    // LDAP
    // ----------------------------------------------------------------------

    /**
     * Handle the login process by sending the user credentials to the server.
     * Store the JWT token in the local storage if login is successful.
     *
     * @param {string} username - The username entered by the user.
     * @param {string} password - The password entered by the user.
     * @returns {Promise<void>}
     *
     */
    async submitLogin(username, password) {
        console.log("Submit login:", username, password);

        let response;
        try {
            response = await this._requestManager.send_post_request({
                "event_name": 'login',
                "username": username,
                "password": password
            }, "application/json", this._uri);
        } catch (error) {
            console.error("Error during login request:", error);
            this._showActionResult(response.error);
            return;
        }

        console.log("Login status:", this._requestManager.status);
        let token = "";
        if (this._requestManager.status === 200) {
            // Save the token in the local storage
            token = await this.storeToken(response);
            this.#updateAuthenticatedSection(response.content);
            this.#updateDocumentsManager();
        }

        if (token === "") {
            this._showActionResult(response.error);
        }
    }

    // ----------------------------------------------------------------------


    /**
     * Handle the login process by sending the user credentials to the server.
     * Store the JWT token in the local storage if login is successful.
     *
     * @param {string} token -
     * @returns {Promise<void>}
     *
     */
    async submitLogout(token) {
        console.log("Submit logout:", token);

        let response;
        try {
            response = await this._requestManager.send_post_request({
                "event_name": 'logout',
                "token": token,
            }, "application/json", this._uri);
        } catch (error) {
            console.error("Error during logout request: ", error);
            this._showActionResult(response.error);
            return;
        }

        console.log("Logout status: ", this._requestManager.status);
        if (this._requestManager.status === 200) {
            // Remove the token of the local storage
            this.removeToken();
            window.location.reload();
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Handles the login submission process.
     *
     * Retrieves the username and password from input fields, closes the login dialog,
     * and submits the credentials via the `submitLogin` method.
     *
     * @param {string} usernameInputId - The ID of the username input field.
     * @param {string} passwordInputId - The ID of the password input field.
     *
     */
    submitLoginDialog(usernameInputId = "username_input", passwordInputId = "password_input") {
        const username = document.getElementById(usernameInputId).value;
        const password = document.getElementById(passwordInputId).value;

        // Close the login dialog before submitting
        close_dialog('login_dialog');

        // Submit the login credentials via the AuthenticationManager
        this.submitLogin(username, password);
    }

    // ----------------------------------------------------------------------

    /**
     * Handle authentication on page load by checking if a token is stored.
     * If a token is found, verify its validity with the server.
     *
     */
    async handleAuthenticationOnLoad() {
        document.getElementById("anonymous_section").style.display = '';
        document.getElementById("authenticated_section").style.display = 'none';

        const token = this.getToken();
        if (token) {
            const status = await this.checkToken(token);
            if (status === 200) {
                console.log("Token is valid:", token);
                const response = await this._requestManager.send_post_request({
                    "token": token
                }, "application/json", this._uri);
                this.#updateAuthenticatedSection(response.content);
                this.#updateDocumentsManager();

            } else {
                console.log("Token is invalid, removing...");
                this.removeToken();
            }
        } else {
            console.log("No token found.");
        }
    }

    // ----------------------------------------------------------------------
    // Private Methods
    // ----------------------------------------------------------------------

    #updateDocumentsManager() {
        if (!window.docManager) {
            console.error("No docManager is attached to window.")
        } else {
            window.docManager.instantiateAsideManager();
            window.docManager.instantiateSortaTable();
        }
    }

    /**
     * Updates the UI sections after authentication.
     * Safely sets the authenticated content and manages the visibility of sections.
     *
     * @param {string} content - The content to display in the authenticated section.
     *
     */
    #updateAuthenticatedSection(content) {

        if (!content || content.trim() === "") {
            console.error("Content is empty. Aborting the update of the authenticated section.");
            return;
        }

        const authContentElement = document.getElementById("authenticated_content");
        const anonymousSection = document.getElementById("anonymous_section");
        const authenticatedSection = document.getElementById("authenticated_section");

        if (authContentElement && anonymousSection && authenticatedSection) {
            // Clear any previous content safely
            authContentElement.textContent = "";
            // Insert new content safely
            authContentElement.insertAdjacentHTML('beforeend', content);
            anonymousSection.style.display = 'none';
            authenticatedSection.style.display = '';
        } else {
            console.error("Failed to find one or more required DOM elements for authentication update.");
        }
    }

}
