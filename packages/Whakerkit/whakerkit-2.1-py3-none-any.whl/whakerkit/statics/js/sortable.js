import { AsideManager } from './doc_details.js';
import { SortaTable } from '../../../whakerexa/wexa_statics/js/wexa.js';

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

export class DocumentsSortaTable extends SortaTable {
    constructor(tableId) {
        super(tableId);
    }

    // ----------------------------------------------------------------------
    // Override methods or add new features
    // ----------------------------------------------------------------------

    /**
     * Attaches event listeners to table headers with the class 'sortable'.
     *
     * Override parent to close details of the aside element when a button in
     * a header is clicked.
     *
     */
    attachSortListeners() {
        if (!this._tableElt) {
            return;
        }
        // Call parent method to attach sort listeners
        super.attachSortListeners();

        // Add logic to close the aside details panel when a sort event is triggered
        const sortButtons = this._tableElt.querySelectorAll(this._className);

        sortButtons.forEach(button => {
            button.addEventListener('click', (event) => {
                // Check if asideManager is defined and is an instance of AsideManager
                if (typeof window.asideManager === "object" && window.asideManager instanceof AsideManager) {
                    window.asideManager.closeDetails();
                }
            });
        });
    }

}
