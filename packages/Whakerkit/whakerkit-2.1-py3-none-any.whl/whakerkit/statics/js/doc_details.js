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
 * AsideManager class handles the display of document details
 * in an aside element on the page. It listens for events and updates the
 * aside content based on the selected document.
 */
export class AsideManager {
    // Protected members
    #asideElement;
    #currentDocumentId;

    constructor() {
        this.#asideElement = document.getElementById('doc_aside');
        this.#currentDocumentId = null;
        
        // Dynamic -- Available in the page only after authentication
        this.filenameElement = undefined;
        this.authorElement = undefined;
        this.filetypeElement = undefined;
        this.dateElement = undefined;
        this.descriptionElement = undefined;
        this.downloadsElement = undefined;
    }

    // ----------------------------------------------------------------------

    /**
     * Initializes the AsideManager when the DOM content is fully loaded.
     *
     * It listens for the 'DOMContentLoaded' event and calls the method
     * to attach specific event listeners related to the AsideManager.
     *
     * @returns {void}
     *
     */
    handleAsideManagerOnLoad() {
        document.addEventListener('DOMContentLoaded', () => {
            this.attachAsideListeners();
        });
    }

    // ----------------------------------------------------------------------

    /**
     * Attaches event listeners to the body for managing clicks related
     * to the AsideManager's functionality.
     *
     * This method listens for click events on the body element and
     * delegates them to the handleBodyClick method to handle specific
     * click actions.
     *
     * @returns {void}
     *
     */
    attachAsideListeners() {
        document.querySelector('body').addEventListener('click', (event) => {
            this.handleBodyClick(event);
        });
    }

    // ----------------------------------------------------------------------

    /**
     * Handles click events on the body element.
     * Closes the details if the click is outside of specified elements.
     *
     * @param {Event} event - The event object triggered by a click.
     *
     */
    handleBodyClick(event) {
        const target = event.target;
        console.debug(target);

        // If the clicked element is not an <img>, <button>, <a>, or <span>
        if (!['img', 'button', 'a', 'span', 'checkbox', 'input'].includes(target.localName)) {
             this.closeDetails();
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Displays details of a document in the aside element.
     *
     * @param {string} documentId - The ID of the document to show details for.
     *
     */
    showDetailsPREVIOUS(documentId) {
        // Same document... nothing to do.
        if (this.#currentDocumentId === documentId) {
            return;
        }
        const row = document.getElementById(documentId);
        if (row) {
            // Find the table element that contains this row
            const table = row.closest('table');

            // Find the header cells (<th>) to identify the column names
            const headers = table.querySelectorAll('thead th');

            // Get the <td> elements (cells) of the row
            const cells = row.getElementsByTagName('td');

            // Create an object to store document details
            let documentDetails = {};

            // Loop through each header to find its corresponding value in the row
            headers.forEach((header, index) => {
                // Get the button inside the header and its data-sort attribute
                const button = header.querySelector('button.sortatable');
                const columnName = button ? button.getAttribute('data-sort') : null;

                // Get the content from the corresponding cell in the row
                const cellValue = cells[index].textContent.trim();

                // Map the column name to the cell value
                documentDetails[columnName] = cellValue;
            });

            // Update the current document ID
            this.#currentDocumentId = documentId;

            // Open details in the aside panel
            this.openDetails(
                documentDetails['filename'] || '',
                documentDetails['author'] || '',
                documentDetails['filetype'] || '',
                documentDetails['date'] || '',
                documentDetails['description'] || '',
                documentDetails['downloads'] || 0
            )

        } else {
            console.error("Could not show details of document: ", documentId);
        }
    }
    showDetails(documentId) {
        // Same document... nothing to do.
        if (this.#currentDocumentId === documentId) {
            return;
        }
        const row = document.getElementById(documentId);
        if (row) {
            // Find the table element that contains this row
            const table = row.closest('table');

            // Find the header cells (<th>) to identify the column names
            const headers = table.querySelectorAll('thead th');

            // Get the <td> elements (cells) of the row
            const cells = row.getElementsByTagName('td');

            // Create an object to store document details
            let documentDetails = {};

            // Loop through each header to find its corresponding value in the row
            headers.forEach((header, index) => {
                // Get the button inside the header and its data-sort attribute, or fallback to the header id
                const button = header.querySelector('button.sortatable');
                const columnName = button ? button.getAttribute('data-sort') : header.getAttribute('id').replace('_th', '');

                // Get the content from the corresponding cell in the row if it exists
                if (cells[index]) {
                    const cellValue = cells[index].textContent.trim();

                    // Map the column name to the cell value
                    documentDetails[columnName] = cellValue;
                }
            });

            // Update the current document ID
            this.#currentDocumentId = documentId;

            // Open details in the aside panel
            this.openDetails(
                documentDetails['filename'] || '',
                documentDetails['author'] || '',
                documentDetails['filetype'] || '',
                documentDetails['date'] || '',
                documentDetails['description'] || '',
                documentDetails['downloads'] || 0
            );

        } else {
            console.error("Could not show details of document: ", documentId);
        }
    }
    // ----------------------------------------------------------------------

    /**
     * Opens the details of a document in the aside element.
     *
     * @param {string} filename - The filename of the document.
     * @param {string} author - The author of the document.
     * @param {string} filetype - The type of the document.
     * @param {string} date - The date of the document.
     * @param {string} description - The description of the document.
     * @param {number} downloads - The number of downloads of the document.
     *
     */
    openDetails(filename, author, filetype, date, description = '--', downloads = 0) {
        try {
            this.findAllElements();
            this.filenameElement.innerText = filename;
            this.authorElement.innerText = author;
            this.filetypeElement.innerText = filetype;
            this.dateElement.innerText = date;
            this.descriptionElement.innerText = description || '';
            this.downloadsElement.innerText = downloads || 0;

            // Open the details aside and set focus for accessibility
            this.#asideElement.classList.add('open');
            this.#asideElement.focus();
        } catch (e) {
            console.error(e);
        }
    }

    // ----------------------------------------------------------------------

    /**
     * Validates that all required elements for displaying details are present.
     *
     * @returns {boolean} - True if all elements are present, false otherwise.
     *
     */
    findAllElements() {
        this.filenameElement = this.getElementOrThrow('doc_filename_span');
        this.authorElement = this.getElementOrThrow('doc_author_span');
        this.filetypeElement = this.getElementOrThrow('doc_filetype_span');
        this.dateElement = this.getElementOrThrow('doc_date_span');
        this.descriptionElement = this.getElementOrThrow('doc_description_span');
        this.downloadsElement = this.getElementOrThrow('doc_downloads_span');
    }

    // ----------------------------------------------------------------------

    /**
     * Retrieves an element by its ID and throws an error if not found.
     *
     * @param {string} elementId - The ID of the HTML element to retrieve.
     * @returns {HTMLElement} - The retrieved element.
     *
     */
    getElementOrThrow(elementId) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.log('Element not found: ', elementId);
            throw new Error(`Element with ID ${elementId} not found.`);
        }
        return element;
    }

    // ----------------------------------------------------------------------

    /**
     * Closes the document details aside element.
     *
     */
    closeDetails() {
        if (this.#asideElement && this.#asideElement.classList.contains('open')) {
            this.#asideElement.classList.remove('open');
            this.#asideElement.blur();
            this.#currentDocumentId = null;
        }
    }
}
