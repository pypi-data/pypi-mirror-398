# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.filters.tests.test_basefilters.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filters tests for the base filters system.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io

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

    -------------------------------------------------------------------------

"""

import unittest

from whakerkit.filters import BaseComparator
from whakerkit.filters import StringComparator
from whakerkit.filters import BaseFilters

# ---------------------------------------------------------------------------


class TestBaseFilters(unittest.TestCase):

    def test_instantiation(self):
        """Test BaseFilters init."""
        obj = object()
        base_filters = BaseFilters(obj)
        self.assertEqual(base_filters._obj, obj)

    # -----------------------------------------------------------------------

    def test_test_args(self):
        comparator = BaseComparator()
        with self.assertRaises(KeyError):
            BaseFilters.test_args(comparator, invalid_arg=1)

    # -----------------------------------------------------------------------

    def test_fix_logic_bool(self):
        result = BaseFilters.fix_logic_bool()
        self.assertEqual(result, "and")

        kwargs = {"logic_bool": "and"}
        result = BaseFilters.fix_logic_bool(**kwargs)
        self.assertEqual(result, "and")

        kwargs = {"logic_bool": "invalid"}
        with self.assertRaises(ValueError):
            BaseFilters.fix_logic_bool(**kwargs)

    # -----------------------------------------------------------------------

    def test_fix_functions(self):
        """Test BaseFilters fix_functions."""
        # no kwargs
        comparator = BaseComparator()
        result = BaseFilters.fix_functions(comparator)
        self.assertEqual(result, [])

        # valid non-empty kwargs
        comparator = StringComparator()
        kwargs = {'exact': "10", 'contains': "0"}
        result = BaseFilters.fix_functions(comparator, **kwargs)
        self.assertEqual(
            result,
            [(comparator.get('exact'), "10", False), (comparator.get('contains'), "0", False)])

        # valid non-empty kwargs with 'not'
        kwargs = {'not_exact': "10", 'contains': "0"}
        result = BaseFilters.fix_functions(comparator, **kwargs)
        self.assertEqual(
            result,
            [(comparator.get('exact'), "10", True), (comparator.get('contains'), "0", False)])

        # an invalid function name is ignored
        kwargs = {'invalid': "10"}
        result = BaseFilters.fix_functions(comparator, **kwargs)
        self.assertEqual(result, [])

        # an invalid function value is not controlled
        kwargs = {'exact': 10}
        result = BaseFilters.fix_functions(comparator, **kwargs)
        self.assertEqual(result, [(comparator.get('exact'), 10, False)])
