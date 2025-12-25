"""
:filename: whakerkit.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org

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

# Import local config
from .config import WhakerKitSettings
from .error import WhakerkitErrorMiddleware
from .po import set_language
from .po import _
from .po import get_msg

# Declare a default settings instance to be used in the whole application
sg = WhakerKitSettings()

# Set the default language for messages in pages
set_language(sg.lang)

# ---------------------------------------------------------------------------


def initialize(config_path: str, root_path : str | None = None) -> WhakerKitSettings:
    """Fix custom settings from the given JSON file.

    :param config_path: (str) Path to the JSON configuration file.
    :param root_path: (str | os.PathLike): Project root.
        Converted to an absolute, normalised path.
    :raises: TypeError: if root_path is not a valid path or os.PathLike.
    :return: Global 'sg'

    """
    logging.info(f"Initializing WhakerKit with configuration file: {config_path} "
                 f"and hosting absolute path: {root_path}")
    global sg
    from whakerkit.config.settings import WhakerKitSettings
    sg = WhakerKitSettings(config_path, root_path)
    # Set language AFTER settings are loaded
    set_language(sg.lang)
    logging.info(" ... settings successfully loaded.")
    return sg

# ---------------------------------------------------------------------------


from .components import *
from .connection import *
from .documents import *
from .filters import *
from .nodes import *
from .responses import *
from .uploads_manager import WhakerKitDocsManager

# ---------------------------------------------------------------------------


__version__ = "2.1"
__copyright__ = 'Copyright (c) 2024-2025 Brigitte Bigi, CNRS, Laboratoire Parole et Langage, Aix-en-Provence, France'
__all__ = (
    "WhakerKitDocsManager",
    "WhakerkitErrorMiddleware",
    "set_language",
    "_",
    "__version__",
    "__copyright__",
    "sg"
)
