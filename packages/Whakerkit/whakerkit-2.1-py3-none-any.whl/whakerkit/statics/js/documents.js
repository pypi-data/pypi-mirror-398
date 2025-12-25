import { BaseManager } from '../../../whakerexa/wexa_statics/js/wexa.js'
import { AsideManager } from './doc_details.js';
import { ToggleSelector } from '../../../whakerexa/wexa_statics/js/wexa.js'

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
 * DocumentsManager class manages document-related operations with the server.
 *
 * This class provides methods to upload documents, delete them, and update their
 * descriptions. It encapsulates the communication with the server through a
 * private instance of `RequestManager()` and handles server responses, including
 * error reporting and page reloading. The class also allows customizing error
 * messages for multilingual support.
 *
 * Requirements:
 *  - DocumentsSortaTable(): Used to sort table rows with documents based on the selected column.
 *
 * Attributes:
 *  - errorUnrespondingMessage (public): A customizable string to define the error message when the server is unresponsive.
 *
 * Methods:
 *  - filterDocuments(): Send a request to filter documents based on user-selected criteria.
 *  - resetFilters: Clear the filters of the page.
 *  - incrementDownloads(): Increment the number of downloads of a document.
 *  - sendDocument(): Uploads a document selected in a file input to the server.
 *  - deleteDocument(folder_name): Sends a request to delete a document on the server.
 *  - describeDocument(folder_name, current_description): Opens a dialog allowing the user to modify the description of a document.
 *
 * Usage example:
 *  const docManager = new DocumentsManager();
 *  docManager.sendDocument(); // Uploads a document to the server.
 *
 */
export class DocumentsManager extends BaseManager {

    // Private
    #tableId
    #toggleSelectorId

    // Protected
    _sortaTable
    _toggleSelector

    // Public members
    errorUnrespondingMessage = "The server did not respond to the request.";
    filtersDetailsID = "filters_details";
    documentsDivID  = "documents_div";

    constructor(tableId=null, toggleSelectorId = null) {
        // Call the constructor of BaseManager
        super();

        // Fix a size limit for upload
        this._requestManager.maxFileSize = 100 * 1024 * 1024; // 100 Mb

        // Manage the sortable table -- if there's one
        if (tableId) {
            this.#tableId = tableId;
            this.#toggleSelectorId = toggleSelectorId;
            this.instantiateSortaTable();
        }
    }

    // ----------------------------------------------------------------------
    // Methods for this class
    // ----------------------------------------------------------------------

    instantiateSortaTable() {
        // Dynamic import: import only if a sortable table is intended to be used
        // Create a new SortaTable instance and attach event listeners after the page loads
        if (this.#tableId) {  // && typeof SortaTable !== 'undefined') {
            import('./sortable.js').then(({ DocumentsSortaTable }) => {
                this._sortaTable = new DocumentsSortaTable(this.#tableId);
                this._sortaTable.attachSortListeners();
                if (this.#toggleSelectorId) {
                    this._toggleSelector = new ToggleSelector("./whakerexa/wexa_statics/icons/", this.#toggleSelectorId);
                    this._toggleSelector.handleInputsOnLoad();
                    this._sortaTable.toggleColumnVisibility(this._toggleSelector.getCheckboxes());
                }
            })
            .catch((error) => {
                console.error('Error importing DocumentsSortaTable:', error);
            });
        }
    }

    /**
     * Initializes the AsideManager instance and attaches listeners if necessary.
     */
    instantiateAsideManager() {
        if (typeof window.asideManager === "object" && window.asideManager instanceof AsideManager) {
            window.asideManager = new AsideManager();
            window.asideManager.attachAsideListeners();
            console.log("Assigned a new AsideManager() to the window.");
        } else {
            console.error("no asideManager assigned to the window.");
        }
    }

    /**
     * Update columns visibility depending on the checked boxes.
     *
     */
    updateColumns() {
        if (!this._sortaTable) return;
        this._sortaTable.toggleColumnVisibility(
            this._toggleSelector.getCheckboxes()
        );
    }

    getToggleSelector() {
        return this._toggleSelector;
    }

    // ----------------------------------------------------------------------
    // Actions on all documents
    // ----------------------------------------------------------------------

    /**
     * Send a request to filter documents based on user-selected criteria.
     *
     * This method gathers the selected filters and conditions from the HTML page,
     * including filetypes, authors, date range, and description filters. It then
     * sends these filters as a POST request to the server, along with a security
     * token stored in localStorage.
     *
     * The response from the server is logged or handled accordingly.
     *
     * @async
     * @returns {void}
     *
     */
    async filterDocuments() {
        console.log(" **************** Filter Documents *************** ");
        let respError = "";
        let respInfo = "";

        // Get the filters and conditions from the HTML
        let conditions = this.#getSelectedConditions();
        let filters = this.#getSelectedFilters();
        console.debug(conditions);
        console.debug(filters);

        // Send the filters to the server
        const response = await this._requestManager.send_post_request({
            "event_name": 'filter_documents',
            "filters": filters,
            "conditions": conditions
        }, "application/json", this._uri)
        .then(response => {
            console.debug("HTTP Status: " + this._requestManager.status);
            // Change the page content: displays only the filtered documents
            if (this._requestManager.status === 200) {
                respInfo = response.info;
                this.#updateDocuments(response.content);
            } else {
                // Controlled error
                respError = response.error;
            }
        })
        .catch(error => {
            // Handle any request or network error
            respError = error.toString();
        });

        this._showActionResult(respError, respInfo, false);
    }

    // ----------------------------------------------------------------------

    /**
     * Clear all filters on the page and reload.
     *
     * @returns {void}
     *
     */
    resetFilters() {
        console.log(" **************** reset Filters *************** ");

        this.clearEntriesInContainer(this.filtersDetailsID);
        window.location.reload();
    }

    // ----------------------------------------------------------------------

    /**
     * Clear all input and select elements within a specific container,
     * resetting them to their default values.
     *
     * @param {string} containerId - The ID of the container (div) within which the filters are reset.
     * @returns {void}
     *
     */
    clearEntriesInContainer(containerId) {

        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container with ID '${containerId}' not found.`);
            return;
        }

        // Reset all checkboxes in the container
        container.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            checkbox.checked = checkbox.defaultChecked;
        });

        // Reset all radio buttons in the container
        container.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.checked = radio.defaultChecked;
        });

        // Clear all text inputs (including date fields) in the container
        container.querySelectorAll('input[type="text"]').forEach(textInput => {
            textInput.value = textInput.defaultValue || '';
        });

        // Reset select elements (dropdowns) in the container
        container.querySelectorAll('select').forEach(select => {
            select.selectedIndex = 0; // Set to the first option
        });

        // Optionally, log to confirm the reset
        console.log(`Filters in container with ID '${containerId}' have been reset.`);
    }

    // ----------------------------------------------------------------------
    // Actions on a single document
    // ----------------------------------------------------------------------

    /**
     * Increment the number of downloads of a document and update the element if applicable.
     *
     * This function sends a request to the server to increment the download count of a document.
     * It opens the document in a new window and updates the download count in the table if
     * the table contains a row corresponding to the document folder name.
     *
     * @async
     * @param {string} href - The URL of the document to be opened.
     * @param {string} folder_name - The unique identifier of the document (also used as the row ID in the table).
     * @return {Promise<void>} - Returns a Promise that resolves when the process is complete.
     *
     */
    async incrementDownloads(href, folder_name) {
        console.log(" **************** Increment Document *************** ");
        console.log(folder_name);
        let respError = "";

        // Check if asideManager is defined and is an instance of AsideManager
        if (typeof window.asideManager === "object" && window.asideManager instanceof AsideManager) {
            window.asideManager.closeDetails();
        }

        // Open the document in a new window
        window.open(href);

        try {
            // Send a request to the server to increment the number of downloads
            const response = await this._requestManager.send_post_request({
                "event_name": 'increment_downloads',
                "folder_name": folder_name,
            }, "application/json", this._uri);

            console.debug("Status: " + this._requestManager.status);
            // If there's an error in the response
            respError = response.error || "";

            if (this._requestManager.status === 200 && response.hasOwnProperty("downloads")) {
                let nb = response.downloads;

                // Find index of download columns
                const thead = document.querySelector('#' + this.#tableId + ' thead');
                let downloadsColumnIndex = -1;
                const headerCells = thead.querySelectorAll('th');
                headerCells.forEach((th, index) => {
                    if (th.id === 'downloads_th' || th.getAttribute('data-sort') === 'downloads') {
                        downloadsColumnIndex = index;
                    }
                });
                if (downloadsColumnIndex === -1) {
                    console.error("Downloads column not found.");
                    return;
                }

                // Get the element row corresponding to the document's folder_name (if it exists)
                const documentRow = document.getElementById(folder_name);
                    if (documentRow) {
                        const downloadCell = documentRow.querySelectorAll('td')[downloadsColumnIndex];
                        if (downloadCell) {
                            downloadCell.textContent = nb;
                            console.log(`Updated downloads count for document ${folder_name} to ${nb}.`);
                        } else {
                            console.error(`Download cell not found for document ${folder_name}`);
                        }
                    } else {
                        console.error(`No row found for document ${folder_name}`);
                    }
                }

        } catch (error) {
            // Handle any request or network error
            respError = error.toString();
        }

        // Display the result of the action (success or failure)
        this._showActionResult(respError, "", false);
    }

    // ----------------------------------------------------------------------

    /**
     * Uploads a document selected in the file input to the server.
     *
     * This function retrieves the file from the input element with id="file_input"
     * and sends it to the server using an asynchronous request. The server's response
     * is handled to detect any errors, which are displayed if they occur. If the upload
     * is successful, the page may be reloaded. After the operation, the input field is
     * cleared to reset the file selection.
     *
     * HTML Requirement:
     *  - An <input> element with id="file_input" for file selection.
     *
     * @async
     * @returns {Promise<void>} - The promise that resolves when the file upload completes.
     *
     */
    async sendDocument() {
        console.log(" **************** Send Document *************** ");
        let respError = "";

        // Get the input element
        let input = document.getElementById("file_input");

        open_dialog('wait_dialog', true);
        document.body.style.cursor = 'wait';

        // Send the file to the server
        try {
            const response = await this._requestManager.upload_file(
                input,
                "application/json",
                localStorage.getItem('token'),
                this._uri
            );

            if (!response) {
                respError = this.errorUnrespondingMessage;
            } else if (response.error) {
                respError = response.error;
            }
        } catch (error) {
            // Handle any request or network error
            respError = error.toString();
        }

        document.body.style.cursor = 'default';
        close_dialog('wait_dialog');

        // See the result: error or reload
        this._showActionResult(respError);
        // Clean input value -- for the browser to "forget" the actual file
        input.value = "";
    }

    // ----------------------------------------------------------------------

    /**
     * Deletes a specified document from the server.
     *
     * This function sends an asynchronous POST request to the server to delete the
     * document identified by the given folder name. The server's response is then
     * handled, and either an error message is displayed or the page is reloaded based
     * on the outcome. The user's authentication token is included in the request for
     * authorization.
     *
     * @param {string} folder_name - The name of the document folder to delete.
     *
     * @async
     * @returns {void}
     *
     */
    async deleteDocument(folder_name) {
        console.log(" **************** Delete Document *************** ");
        let respError;

        // Send the folder_name to the server
        try {
            const response = await this._requestManager.send_post_request({
                "event_name": 'delete_document',
                "folder_name": folder_name,
                "token": localStorage.getItem('token')
            }, "application/json", this._uri);
            respError = response.error;
        } catch (error) {
            // Handle any request or network error
            respError = error.toString();
        }

        this._showActionResult(respError, "", true);
    }

    // --------------------------------------------------------------------------

    /**
     * Opens a dialog to set a new description for a specified document folder.
     *
     * This function dynamically updates an existing HTML dialog with the provided
     * folder name and current description. It then allows the user to modify the
     * description and submit the changes. Once confirmed, the new description is
     * sent to the server via an asynchronous POST request. If the user cancels,
     * the dialog is simply closed without any action.
     *
     * HTML Requirements:
     *  - A <dialog> element with id="description_dialog".
     *  - A <textarea> element with id="new_description_field" for inputting the new description.
     *  - A <span> element with id="folder_name_span" to display the folder name.
     *
     * @param {string} documentId - The name of the folder/document being described.
     * @param {string} current_description - The current description of the document to prefill in the textarea.
     *
     * @async
     * @returns {void}
     *
     */
    async describeDocument(documentId, current_description = "") {
        console.log(" **************** Describe Document *************** ");

        // Get the dialog to enter the new description
        let dialog = document.getElementById('description_dialog');
        if (!dialog) {
            console.error("Dialog 'description_dialog' is missing.");
            return
        }

        // Find the index of the "Description" column in the <thead>
        const thead = document.querySelector('#' + this.#tableId + ' thead');
        let descriptionColumnIndex = -1;
        const headerCells = thead.querySelectorAll('th');
        headerCells.forEach((th, index) => {
            if (th.id === 'description_th' || th.getAttribute('data-sort') === 'description') {
                descriptionColumnIndex = index;
            }
        });
        if (descriptionColumnIndex === -1) {
            console.error("Description column not found.");
            return;
        }

        // Get fields in the dialog
        let descriptionField = dialog.querySelector('#new_description_field');
        let folderNameSpan = dialog.querySelector('#folder_name_span');
        if (!descriptionField) {
            console.error("Field 'new_description_field' is missing in description_dialog.");
            return
        } else if (!folderNameSpan) {
            console.error("Span 'folder_name_span' is missing in description_dialog.");
            return
        } else {
            folderNameSpan.textContent = documentId;
            // Retrieve the current description from the table cell
            const documentRow = document.getElementById(documentId);
            if (documentRow) {
                const descriptionCell = documentRow.querySelectorAll('td')[descriptionColumnIndex];
                current_description = descriptionCell ? descriptionCell.textContent.trim() : "";
                descriptionField.value = current_description;
            } else {
                console.warn(`No row found for document ID: ${documentId}`);
                descriptionField.value = "";
            }
        }

        // Open the modal dialog, already includes a close button.
        open_dialog('description_dialog', true);
        this.currentDescriptionLength();
        /* Suggestion:
        const confirmButton = dialog.querySelector('#confirm');
        // remplace l'élément pour retirer les anciens gestionnaires
        confirmButton.replaceWith(confirmButton.cloneNode(true));
        dialog.querySelector('#confirm').addEventListener('click', async () => {
            // code de confirmation
        });*/

        // Manage confirm button
        let respError;
        dialog.querySelector('#confirm').addEventListener('click', async () => {
            let newDescription = descriptionField.value;
            dialog.close();
            // Send the folder_name and description to the server
            try {
                const response = await this._requestManager.send_post_request({
                    "event_name": 'describe_document',
                    "folder_name": documentId,
                    "description": newDescription,
                    "token": localStorage.getItem('token')
                }, "application/json", this._uri);
                respError = response.error;
            } catch (error) {
            // Handle any request or network error
            respError = error.toString();
            }

            this._showActionResult(respError);
        });
    }

    // ----------------------------------------------------------------------

    /**
     * Updates the number of characters in the description dialog.
     *
     * This function retrieves the description dialog, verifies its presence,
     * checks if the dialog is opened, and updates the character count of the
     * entered description in the associated span element.
     *
     * @returns {void}
     *
     */
    currentDescriptionLength() {
        // Get the dialog element to enter the new description
        let dialog = document.getElementById('description_dialog');
        if (!dialog) {
            console.error("Dialog 'description_dialog' is missing.");
            return;
        }

        // Check if the dialog is opened
        if (!dialog.open) {
            console.warn("Dialog 'description_dialog' is not open.");
            return;
        }

        // Get the textarea with the new description
        const descriptionField = dialog.querySelector('#new_description_field');
        if (!descriptionField) {
            console.error("Textarea 'new_description_field' is missing.");
            return;
        }

        // Get the current length of the description
        const currentLength = descriptionField.value.length;

        // Get the span element that displays the current description length and update its content
        const spanElt = dialog.querySelector('#new_description_span');
        if (!spanElt) {
            console.error("Span element 'new_description_span' is missing.");
        } else {
            // Update the character count in the span
            spanElt.textContent = currentLength;
        }
    }

    // ----------------------------------------------------------------------
    // Private
    // ----------------------------------------------------------------------

    /**
     * Get selected filters from the HTML elements.
     *
     * This function retrieves the selected values for filters such as file types,
     * authors, description text, and deposit dates from the page's HTML input elements.
     *
     * @returns {Object} An object containing the selected filters:
     * - filetype: An array of selected file types (e.g., ["pdf", "html"]).
     * - authors: An array of selected authors (e.g., ["Prenom-Nom"]).
     * - dates: An object with start and end dates for the deposit:
     *   { start: 'YYYY', end: 'YYYY' }.
     * - description: The text entered by user in the description input field.
     *
     */
    #getSelectedFilters() {

        const filters = {
            filetype: [],  // To store selected file types
            authors: [],   // To store selected authors
            // Get selected start and end dates
            dates: {
                start: document.getElementById('date_min_input')?.value || '',
                end: document.getElementById('date_max_input')?.value || ''
            },
            // Get entered text for description -- also applied to filename
            description: document.getElementById('description_input')?.value || ''
        };

        // Get checked filetypes
        window.toggleSelectorFiletype.getCheckboxes().forEach(input => {
            // Push file type based on the checkbox ID
            if (input.checked) {
                filters.filetype.push(input.id.replace('_input', ''));
            }
        });

        // Get checked authors
        window.toggleSelectorAuthor.getCheckboxes().forEach(input => {
            // Push author name based on the checkbox ID
            if (input.checked) {
                filters.authors.push(input.id.replace('_input', ''));
            }
        });

        return filters;
    }

    // ----------------------------------------------------------------------

    /**
     * Get selected conditions of filters.
     *
     * This function retrieves the selected conditions from the radio buttons
     * for applying filters ('all conditions' or 'at least one condition'),
     * as well as the condition for how to apply the description filter.
     *
     * @returns {Object} An object containing the selected conditions:
     * - general: The condition for general filters (e.g., true or false).
     *   Defaults to true if no input is found.
     * - description: The selected condition for the description filter
     *   (e.g., "contains", "not_exact"). Defaults to "acontains".
     * - switch_description: A boolean representing the state of the description switch
     *   (true for "AND" by default, false for "OR").
     */
    #getSelectedConditions() {
        const conditions = {};

        // Retrieve the general condition (true/false)
        const generalInput = document.querySelector('input[name="general_condition"]:checked');
        if (generalInput === null) {
            console.error('Input not found: general_condition. Defaulting to "true".');
            conditions.general_condition = true;
        } else {
            conditions.general_condition = generalInput.value === 'true';
        }

        // Retrieve the description condition (e.g., "contains", "not_exact")
        const descriptionInput = document.getElementById('description_condition');
        if (descriptionInput === null) {
            console.error('Input not found: description_condition. Defaulting to "acontains".');
            conditions.description_condition = 'acontains';
        } else {
            conditions.description_condition = descriptionInput.value;
        }

        // Retrieve the AND/OR switch for description filtering
        const switchInput = document.getElementById('switch_description_label')?.querySelector('input[type="checkbox"]');
        if (switchInput === null) {
            console.error('Input not found: switch_description. Defaulting to "AND" (true).');
            conditions.switch_description = true;
        } else {
            conditions.switch_description = switchInput.checked;
        }

        return conditions;
    }
    // ----------------------------------------------------------------------

    /**
     * Replace the table of documents and re-attach table listeners.
     *
     * @param {string} newTableContent - HTML content with new documents.
     *
     */
    #updateDocuments(newTableContent) {
        const documentsDiv = document.getElementById(this.documentsDivID);
        documentsDiv.innerHTML = newTableContent;

        // Re-attach listeners
        console.log(" --------->>>>>>>>>> updateDocuments <<<<<<<<<<<<---------")
        this.instantiateAsideManager();
        this.instantiateSortaTable();
    }

}
