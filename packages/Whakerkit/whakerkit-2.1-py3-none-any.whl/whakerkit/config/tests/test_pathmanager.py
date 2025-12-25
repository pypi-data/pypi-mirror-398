"""
:filename: whakerkit.tests.test_pathmanager.py
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

import unittest


from whakerkit.config.pathmanager import PathManager


class TestPathManager(unittest.TestCase):

    def test_init(self):
        with self.assertRaises(TypeError):
            PathManager(None)
        PathManager("toto")

    def test_compute_path(self):
        # Case 1: Local installation
        root_path_local = "/mnt/c/users/SOMEPATH/website"
        whakerkit_local = "/mnt/c/users/SOMEPATH/website/whakerkit"

        pm_local = PathManager(root_path_local)
        self.assertEqual("whakerkit", pm_local.compute_relative_path(whakerkit_local))

        # Case 2: Virtual environment within website folder
        root_path_venv_local = "/mnt/c/users/SOMEPATH/website"
        whakerkit_venv_local = "/mnt/c/users/SOMEPATH/website/venv/lib/python3.11/site-packages/whakerkit"

        pm_venv_local = PathManager(root_path_venv_local)
        self.assertEqual(
            "venv/lib/python3.11/site-packages/whakerkit",
            pm_venv_local.compute_relative_path(whakerkit_venv_local))

        # Case 3: Virtual environment elsewhere
        root_path_venv_elsewhere = "/mnt/c/users/SOMEPATH/website"
        whakerkit_venv_elsewhere = "/mnt/c/otherpath/envs/myenv/lib/python3.11/site-packages/whakerkit"

        pm_venv_elsewhere = PathManager(root_path_venv_elsewhere)
        self.assertEqual(
            "../../../otherpath/envs/myenv/lib/python3.11/site-packages/whakerkit",
            pm_venv_elsewhere.compute_relative_path(whakerkit_venv_elsewhere))
