# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.pathmanager.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: The WhakerKit utility for relative - absolute path management.

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

import os
import sysconfig

# ---------------------------------------------------------------------------

class PathManager:
    """Utility to derive project-relative paths.

    Converts absolute filesystem locations to paths relative to
    *root_path*.  Handles virtual-environment layouts and normalises all
    path separators to the forward-slash form.

    """

    def __init__(self, root_path):
        """Create a new :class:`PathManager`.

        :param root_path: (str | os.PathLike): Project root.
            Converted to an absolute, normalised path.
        :raises: TypeError: if root_path is not a valid path or os.PathLike.

        """
        self.__root_path = os.path.abspath(root_path)

    # -----------------------------------------------------------------------

    def get_root_path(self):
        """Return the absolute project root path.

        :return: (str) Absolute path initially supplied at construction.

        """
        return self.__root_path

    # -----------------------------------------------------------------------

    def compute_relative_path(self, target_path):
        """Return *target_path* expressed relative to the project root.

        If *target_path* lies within a virtual-environment ``site-packages``
        directory, the result climbs from the root to that directory before
        descending to the target.  All directory separators are converted to
        ``'/'``.

        :param target_path: (str | os.PathLike): Absolute or relative path to convert.
        :return: (str) Path to *target_path* relative to *root_path*.
        :raises: RuntimeError: No meaningful relative path could be computed
                (e.g., unrelated drives on Windows and not inside ``site-packages``).

        """
        target_path = os.path.abspath(target_path)

        # Attempt to compute a direct relative path
        try:
            relative_path = os.path.relpath(target_path, self.__root_path)
            return relative_path.replace("\\", "/")
        except ValueError:
            pass  # paths are on different drives (Windows specific)

        # Handle virtual environment scenario
        site_packages = sysconfig.get_paths()["purelib"]

        if target_path.startswith(site_packages):
            relative_from_site_packages = os.path.relpath(target_path, site_packages)
            # Compute relative path from the root path to the site-packages directory
            relative_to_site_packages = os.path.relpath(site_packages, self.__root_path)

            # Join paths to form a web-compatible relative path
            combined_path = os.path.normpath(os.path.join(relative_to_site_packages, relative_from_site_packages))

            return combined_path.replace("\\", "/")

        raise RuntimeError(f"Unable to compute relative path for: {target_path}")

