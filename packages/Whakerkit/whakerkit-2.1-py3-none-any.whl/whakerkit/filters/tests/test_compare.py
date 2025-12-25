# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.filters.tests.test_compare.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Filters tests, for comparator systems.

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

import datetime
import unittest

from whakerkit.filters import BaseComparator
from whakerkit.filters import StringComparator
from whakerkit.filters import DatetimeComparator
from whakerkit.filters import NumericComparator

# ---------------------------------------------------------------------------


class TestBaseComparator(unittest.TestCase):

    def test_instantiation(self):
        """Test BaseComparator init."""
        comparator = BaseComparator()
        self.assertIsInstance(comparator, BaseComparator)
        self.assertEqual(comparator._methods, {})

        # callable values
        comparator._methods['method1'] = lambda: None
        self.assertTrue(callable(comparator._methods['method1']))

    def test_get_function_names(self):
        """Test BaseComparator get_function_names."""
        comparator = BaseComparator()
        self.assertEqual(comparator.get_function_names(), [])

    def test_get(self):
        """Test BaseComparator get."""
        comparator = BaseComparator()

        # existing function
        comparator._methods['method1'] = lambda: None
        self.assertEqual(comparator.get('method1'), comparator._methods['method1'])

        # non-existing function
        with self.assertRaises(ValueError):
            comparator.get('method2')

    def test_subclassing(self):
        """Test BaseComparator subclass."""
        class SubComparator(BaseComparator):
            pass
        sub_comparator = SubComparator()
        sub_comparator._methods['method1'] = lambda: None
        self.assertEqual(sub_comparator.get_function_names(), ['method1'])
        self.assertIsInstance(sub_comparator, BaseComparator)
        self.assertIsInstance(sub_comparator, SubComparator)

# ---------------------------------------------------------------------------


class TestStringComparator(unittest.TestCase):

    def setUp(self):
        self.expected_methods = {
            'exact': StringComparator.exact,
            'iexact': StringComparator.iexact,
            'aexact': StringComparator.aexact,
            'startswith': StringComparator.startswith,
            'astartswith': StringComparator.astartswith,
            'istartswith': StringComparator.istartswith,
            'endswith': StringComparator.endswith,
            'iendswith': StringComparator.iendswith,
            'aendswith': StringComparator.aendswith,
            'contains': StringComparator.contains,
            'icontains': StringComparator.icontains,
            'acontains': StringComparator.acontains,
            'regexp': StringComparator.regexp
        }

    def test_instantiation(self):
        """Test StringComparator init."""
        sc = StringComparator()
        self.assertIsInstance(sc, StringComparator)
        self.assertIsInstance(sc, BaseComparator)
        self.assertEqual(sc._methods, self.expected_methods)

    def test_check_string(self):
        """Test StringComparator check_string."""
        sc = StringComparator()
        with self.assertRaises(TypeError):
            sc._check_string(None)
        with self.assertRaises(TypeError):
            sc._check_string(123)
        with self.assertRaises(TypeError):
            sc._check_string(bytes('12'))
        self.assertIsNone(sc._check_string("toto"))

    def test_get(self):
        """Test StringComparator inherited get."""
        sc = StringComparator()
        with self.assertRaises(ValueError):
            sc.get('invalid_function')

    def test_get_function_names(self):
        """Test StringComparator inherited get_function_names."""
        sc = StringComparator()
        self.assertEqual(sorted(sc.get_function_names()), sorted(self.expected_methods.keys()))

    def test_exact(self):
        """Test StringComparator exact."""
        sc = StringComparator()

        # valid parameters
        result = sc.exact("abc", "abc")
        self.assertTrue(result)
        result = sc.exact("abc", "ABC")
        self.assertFalse(result)
        result = sc.exact("", "")
        self.assertTrue(result)

        # invalid parameters
        with self.assertRaises(TypeError):
            sc.exact(123, "abc")
        with self.assertRaises(TypeError):
            sc.exact("abc", 123)
        with self.assertRaises(TypeError):
            sc.exact(None, "abc")

    def test_aexact(self):
        """Test StringComparator aexact."""
        sc = StringComparator()

        # valid parameters
        result = sc.aexact("abcé", "abce")
        self.assertTrue(result)
        result = sc.aexact("àéçè", "aece")
        self.assertTrue(result)
        result = sc.aexact("", "")
        self.assertTrue(result)

        # invalid parameters
        with self.assertRaises(TypeError):
            sc.aexact(123, "abc")
        with self.assertRaises(TypeError):
            sc.aexact("abc", 123)
        with self.assertRaises(TypeError):
            sc.aexact(None, "abc")

    def test_iexact(self):
        """Test StringComparator iexact."""
        sc = StringComparator()

        # valid parameters
        result = sc.iexact("abc", "abc")
        self.assertTrue(result)
        result = sc.iexact("abc", "ABC")
        self.assertTrue(result)
        result = sc.iexact("", "")
        self.assertTrue(result)

        # invalid parameters
        with self.assertRaises(TypeError):
            sc.iexact(123, "abc")
        with self.assertRaises(TypeError):
            sc.iexact("abc", 123)
        with self.assertRaises(TypeError):
            sc.iexact(None, "abc")

    def test_startswith(self):
        """Test StringComparator startswith."""
        s1 = "Hello World"

        # True conditions
        s2 = "Hello"
        result = StringComparator.startswith(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.startswith(s1, s2)
        self.assertTrue(result)

        s2 = "Hello World"
        result = StringComparator.startswith(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "World"
        result = StringComparator.startswith(s1, s2)
        self.assertFalse(result)

        s2 = "HELLO World"
        result = StringComparator.startswith(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.startswith(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.startswith(s2, s1)
        with self.assertRaises(TypeError):
            StringComparator.startswith(b"hello", b"hello")

    def test_istartswith(self):
        """Test StringComparator istartswith."""
        s1 = "Hello World"

        # True conditions
        s2 = "Hello"
        result = StringComparator.istartswith(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.istartswith(s1, s2)
        self.assertTrue(result)

        s2 = "Hello World"
        result = StringComparator.istartswith(s1, s2)
        self.assertTrue(result)

        s2 = "HELLO World"
        result = StringComparator.istartswith(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "World"
        result = StringComparator.istartswith(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.istartswith(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.istartswith(s2, s1)
        with self.assertRaises(TypeError):
            StringComparator.istartswith(b"hello", b"hello")

    def test_endswith(self):
        """Test StringComparator endswith."""
        s1 = "Hello World"

        # True conditions
        s2 = "World"
        result = StringComparator.endswith(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.endswith(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "WORLD"
        result = StringComparator.endswith(s1, s2)
        self.assertFalse(result)

        s2 = "Foo"
        result = StringComparator.endswith(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.endswith(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.endswith(s2, s1)

    def test_iendswith(self):
        """Test StringComparator iendswith."""
        s1 = "Hello World"

        # True conditions
        s2 = "World"
        result = StringComparator.iendswith(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.iendswith(s1, s2)
        self.assertTrue(result)

        s2 = "WORLD"
        result = StringComparator.iendswith(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "Foo"
        result = StringComparator.iendswith(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.iendswith(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.iendswith(s2, s1)

    def test_contains(self):
        """Test StringComparator contains."""
        s1 = ""
        s2 = ""
        result = StringComparator.contains(s1, s2)
        self.assertTrue(result)

        s1 = "Hello World"

        # True conditions
        s2 = "World"
        result = StringComparator.contains(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.contains(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "Foo"
        result = StringComparator.contains(s1, s2)
        self.assertFalse(result)

        s2 = "HELLO"
        result = StringComparator.contains(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.contains(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.contains(s2, s1)

    def test_contains(self):
        """Test StringComparator contains."""
        s1 = ""
        s2 = ""
        result = StringComparator.acontains(s1, s2)
        self.assertTrue(result)

        s1 = "héllô Wörld"

        # True conditions
        s2 = "World"
        result = StringComparator.acontains(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.acontains(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "Foo"
        result = StringComparator.acontains(s1, s2)
        self.assertFalse(result)

        s2 = "nöt_fôünd"
        result = StringComparator.acontains(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.acontains(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.acontains(s2, s1)

    def test_icontains(self):
        """Test StringComparator icontains."""
        s1 = "Hello World"

        # True conditions
        s2 = "World"
        result = StringComparator.icontains(s1, s2)
        self.assertTrue(result)

        s2 = ""
        result = StringComparator.icontains(s1, s2)
        self.assertTrue(result)

        s2 = "HELLO"
        result = StringComparator.icontains(s1, s2)
        self.assertTrue(result)

        # False conditions
        s2 = "Foo"
        result = StringComparator.icontains(s1, s2)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.icontains(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.icontains(s2, s1)

    def test_regexp(self):
        """Test StringComparator regexp."""
        sc = StringComparator()
        s = "Hello World"

        # True conditions
        pattern = "Hello"
        result = sc.regexp(s, pattern)
        self.assertTrue(result)

        pattern = "^H"
        result = sc.regexp(s, pattern)
        self.assertTrue(result)

        # False conditions
        pattern = "[0-9]"
        result = sc.regexp(s, pattern)
        self.assertFalse(result)

        # Invalid parameters
        s1 = 123
        s2 = "Hello"
        with self.assertRaises(TypeError):
            StringComparator.regexp(s1, s2)
        with self.assertRaises(TypeError):
            StringComparator.regexp(s2, s1)

# ---------------------------------------------------------------------------


class TestDatetimeComparator(unittest.TestCase):

    def setUp(self):
        self.expected_methods = {
            'equal': DatetimeComparator.equal,
            'gt': DatetimeComparator.gt,
            'ge': DatetimeComparator.ge,
            'le': DatetimeComparator.le,
            'lt': DatetimeComparator.lt,
            'before': DatetimeComparator.le,
            'after': DatetimeComparator.ge
        }

    def test_instantiation(self):
        """Test DatetimeComparator init."""

        sc = DatetimeComparator()
        self.assertIsInstance(sc, DatetimeComparator)
        self.assertIsInstance(sc, BaseComparator)
        self.assertEqual(sc._methods, self.expected_methods)

    def test_check_date(self):
        """Test DateComparator check_date."""
        sc = DatetimeComparator()
        with self.assertRaises(TypeError):
            sc._check_date(None)
        with self.assertRaises(TypeError):
            sc._check_date(123)
        with self.assertRaises(TypeError):
            sc._check_date(bytes('12'))
        self.assertIsNone(sc._check_date(datetime.date(1997, 8, 29)))

    def test_equal(self):
        """Test DatetimeComparator equal."""
        tc = DatetimeComparator()

        # With datetime.date
        d1 = datetime.date(2021, 10, 15)
        d2 = datetime.date(2021, 10, 15)
        result = tc.equal(d1, d2)
        self.assertTrue(result)

        d2 = datetime.date(2022, 10, 15)
        result = tc.equal(d1, d2)
        self.assertFalse(result)

        # With datetime.datetime
        d1 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        result = tc.equal(d1, d2)
        self.assertTrue(result)

        d2 = datetime.datetime(2022, 10, 15, hour=5, minute=5, second=5)
        result = tc.equal(d1, d2)
        self.assertFalse(result)

        # Invalid parameters
        d1 = datetime.date(2021, 10, 15)
        d2 = "Hello"
        with self.assertRaises(TypeError):
            DatetimeComparator.equal(d1, d2)
        with self.assertRaises(TypeError):
            DatetimeComparator.equal(d2, d1)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        with self.assertRaises(TypeError):
            DatetimeComparator.equal(d1, d2)

    def test_lt(self):
        """Test DatetimeComparator lt."""
        tc = DatetimeComparator()

        # With datetime.date
        d1 = datetime.date(2021, 10, 14)
        d2 = datetime.date(2021, 10, 15)
        result = tc.lt(d1, d2)
        self.assertTrue(result)

        result = tc.lt(d2, d1)
        self.assertFalse(result)

        # With datetime.datetime
        d1 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=15, second=15)
        result = tc.lt(d1, d2)
        self.assertTrue(result)

        result = tc.lt(d2, d1)
        self.assertFalse(result)

        # Invalid parameters
        d1 = datetime.date(2021, 10, 15)
        d2 = "Hello"
        with self.assertRaises(TypeError):
            DatetimeComparator.lt(d1, d2)
        with self.assertRaises(TypeError):
            DatetimeComparator.lt(d2, d1)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        with self.assertRaises(TypeError):
            DatetimeComparator.lt(d1, d2)

    # -----------------------------------------------------------------------

    def test_gt(self):
        """Test DatetimeComparator gt."""
        tc = DatetimeComparator()

        # With datetime.date
        d1 = datetime.date(2021, 10, 14)
        d2 = datetime.date(2021, 10, 15)
        result = tc.gt(d2, d1)
        self.assertTrue(result)

        result = tc.gt(d1, d2)
        self.assertFalse(result)

        # With datetime.datetime
        d1 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=15, second=15)
        result = tc.gt(d2, d1)
        self.assertTrue(result)

        result = tc.gt(d1, d2)
        self.assertFalse(result)

        # Invalid parameters
        d1 = datetime.date(2021, 10, 15)
        d2 = "Hello"
        with self.assertRaises(TypeError):
            DatetimeComparator.gt(d1, d2)
        with self.assertRaises(TypeError):
            DatetimeComparator.gt(d2, d1)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        with self.assertRaises(TypeError):
            DatetimeComparator.gt(d1, d2)

    # -----------------------------------------------------------------------

    def test_le_before(self):
        """Test DatetimeComparator le and before."""
        tc = DatetimeComparator()

        # With datetime.date
        d1 = datetime.date(2021, 10, 14)
        d2 = datetime.date(2021, 10, 15)
        result = tc.le(d1, d2)
        self.assertTrue(result)
        result = tc._methods['before'](d1, d2)
        self.assertTrue(result)

        result = tc.le(d2, d1)
        self.assertFalse(result)

        d1 = datetime.date(2021, 10, 15)
        d2 = datetime.date(2021, 10, 15)
        result = tc.le(d2, d1)
        self.assertTrue(result)

        # With datetime.datetime
        d1 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=15, second=15)
        result = tc.le(d1, d2)
        self.assertTrue(result)

        result = tc.le(d2, d1)
        self.assertFalse(result)

        # Invalid parameters
        d1 = datetime.date(2021, 10, 15)
        d2 = "Hello"
        with self.assertRaises(TypeError):
            DatetimeComparator.le(d1, d2)
        with self.assertRaises(TypeError):
            DatetimeComparator.le(d2, d1)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        with self.assertRaises(TypeError):
            DatetimeComparator.le(d1, d2)

    # -----------------------------------------------------------------------

    def test_ge_after(self):
        """Test DatetimeComparator ge and after."""
        tc = DatetimeComparator()

        # With datetime.date
        d1 = datetime.date(2021, 10, 14)
        d2 = datetime.date(2021, 10, 15)
        result = tc.ge(d2, d1)
        self.assertTrue(result)
        result = tc._methods["after"](d2, d1)
        self.assertTrue(result)

        result = tc.ge(d1, d2)
        self.assertFalse(result)

        d1 = datetime.date(2021, 10, 15)
        d2 = datetime.date(2021, 10, 15)
        result = tc.ge(d2, d1)
        self.assertTrue(result)

        # With datetime.datetime
        d1 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=15, second=15)
        result = tc.ge(d2, d1)
        self.assertTrue(result)

        result = tc.ge(d1, d2)
        self.assertFalse(result)

        # Invalid parameters
        d1 = datetime.date(2021, 10, 15)
        d2 = "Hello"
        with self.assertRaises(TypeError):
            DatetimeComparator.ge(d1, d2)
        with self.assertRaises(TypeError):
            DatetimeComparator.ge(d2, d1)
        d2 = datetime.datetime(2021, 10, 15, hour=5, minute=5, second=5)
        with self.assertRaises(TypeError):
            DatetimeComparator.ge(d1, d2)

# ---------------------------------------------------------------------------


class TestNumericComparator(unittest.TestCase):

    def setUp(self):
        self.expected_methods = {
            'equal': NumericComparator.equal,
            'gt': NumericComparator.gt,
            'ge': NumericComparator.ge,
            'le': NumericComparator.le,
            'lt': NumericComparator.lt
        }

    def test_instantiation(self):
        """Test DatetimeComparator init."""
        sc = NumericComparator()
        self.assertIsInstance(sc, NumericComparator)
        self.assertIsInstance(sc, BaseComparator)
        self.assertEqual(sc._methods, self.expected_methods)

    def test_equal(self):
        """Test NumericComparator equal."""
        tc = NumericComparator()

        # With int
        d1 = 15
        result = tc.equal(d1, 15)
        self.assertTrue(result)

        result = tc.equal(d1, 22)
        self.assertFalse(result)

        # With float
        d1 = 2.0
        result = tc.equal(d1, 2.0)
        self.assertTrue(result)

        result = tc.equal(d1, 1.9999999)
        self.assertFalse(result)

        # Invalid parameters
        with self.assertRaises(TypeError):
            NumericComparator.equal(1, 1.0)
        with self.assertRaises(TypeError):
            NumericComparator.equal(1, "1")

    def test_lt(self):
        """Test NumericComparator lt."""
        tc = NumericComparator()

        # With int
        d1 = 15
        result = tc.lt(d1, 30)
        self.assertTrue(result)

        result = tc.lt(30, d1)
        self.assertFalse(result)

        # With float
        d1 = 15.0
        result = tc.lt(d1, 30.0)
        self.assertTrue(result)

        result = tc.lt(30.0, d1)
        self.assertFalse(result)

        # Invalid parameters
        with self.assertRaises(TypeError):
            NumericComparator.lt(15, 15.0)
        with self.assertRaises(TypeError):
            NumericComparator.lt(15, "15")

    # -----------------------------------------------------------------------

    def test_gt(self):
        """Test NumericComparator gt."""
        tc = NumericComparator()

        # With int
        d1 = 15
        result = tc.gt(d1, 10)
        self.assertTrue(result)

        result = tc.gt(10, d1)
        self.assertFalse(result)

        # With float
        d1 = 15.
        result = tc.gt(d1, 10.)
        self.assertTrue(result)

        result = tc.gt(10., d1)
        self.assertFalse(result)

        # Invalid parameters
        with self.assertRaises(TypeError):
            NumericComparator.gt(15, 15.)
        with self.assertRaises(TypeError):
            NumericComparator.gt(15, "15")

    # -----------------------------------------------------------------------

    def test_le(self):
        """Test NumericComparator le."""
        tc = NumericComparator()

        # With int
        d1 = 15
        result = tc.le(d1, 15)
        self.assertTrue(result)
        result = tc.le(d1, 20)
        self.assertTrue(result)

        result = tc.le(20, d1)
        self.assertFalse(result)

        # With float
        d1 = 15.
        result = tc.le(d1, 15.)
        self.assertTrue(result)
        result = tc.le(d1, 20.)
        self.assertTrue(result)

        result = tc.le(20., d1)
        self.assertFalse(result)

        # Invalid parameters
        with self.assertRaises(TypeError):
            NumericComparator.le(15, 15.0)
        with self.assertRaises(TypeError):
            NumericComparator.le(15, "15")

    # -----------------------------------------------------------------------

    def test_ge_after(self):
        """Test DatetimeComparator ge and after."""
        tc = NumericComparator()

        # With int
        d1 = 15
        result = tc.ge(15, 15)
        self.assertTrue(result)
        result = tc.ge(15, 10)
        self.assertTrue(result)

        result = tc.ge(10, d1)
        self.assertFalse(result)

        # With float
        d1 = 15.
        result = tc.ge(15., 15.)
        self.assertTrue(result)
        result = tc.ge(15., 10.)
        self.assertTrue(result)

        result = tc.ge(10., d1)
        self.assertFalse(result)

        # Invalid parameters
        with self.assertRaises(TypeError):
            NumericComparator.ge(15, 15.0)
        with self.assertRaises(TypeError):
            NumericComparator.ge(15, "15")
