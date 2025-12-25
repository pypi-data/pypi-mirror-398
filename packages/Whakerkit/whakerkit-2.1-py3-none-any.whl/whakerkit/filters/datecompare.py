"""
:filename: whakerkit.filters.datecompare.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Comparator system for dates.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io

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

from __future__ import annotations
import datetime

from .basecompare import BaseComparator

# ---------------------------------------------------------------------------


class DatetimeComparator(BaseComparator):
    """Comparison methods for datetime.date or datetime.datetime objects.

    It extends the BaseComparator() and includes methods to check equality,
    less than, less than or equal to, greater than, and greater than or equal
    to between two datetime objects.
    It also includes error handling for type mismatches.

    :example:
    >>> import datetime
    >>> tc = DatetimeComparator()
    >>> tc.equal(datetime.date(2024, 3, 12), datetime.date(2024, 3, 12))
    True
    >>> tc.get('equal')(datetime.date(2024, 3, 12), datetime.date(2024, 3, 12))
    True

    """
    
    _ERROR_TYPES_MISMATCH = "Expected the same datetime types. Got {} and {} instead."

    def __init__(self):
        """Create a DatetimeComparator instance.

        """
        super().__init__()

        # The methods and their corresponding functions on dates
        self._methods['equal'] = DatetimeComparator.equal
        self._methods['le'] = DatetimeComparator.le
        self._methods['lt'] = DatetimeComparator.lt
        self._methods['ge'] = DatetimeComparator.ge
        self._methods['gt'] = DatetimeComparator.gt
        self._methods['before'] = DatetimeComparator.le
        self._methods['after'] = DatetimeComparator.ge

    # -----------------------------------------------------------------------

    @staticmethod
    def _check_date(d: datetime) -> None:
        """Raise TypeError if not a datetime.date or datetime.datetime object.

        :param d: (datetime) A date to be checked
        :raises: TypeError: d is not of the expected type

        """
        if isinstance(d, (datetime.date, datetime.datetime)) is False:
            raise TypeError(f"Expected a datetime. Got {str(type(d))} instead.")

    # -----------------------------------------------------------------------

    @staticmethod
    def equal(d1: datetime, d2: datetime) -> bool:
        """Test if two datetime are equal to each other.

        :param d1: (datetime) Datetime to compare.
        :param d2: (datetime) Datetime to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types

        """
        DatetimeComparator._check_date(d1)
        DatetimeComparator._check_date(d2)
        if type(d1) is type(d2):
            return d1 == d2
        else:
            raise TypeError(DatetimeComparator._ERROR_TYPES_MISMATCH.format(type(d1), type(d2)))

    # -----------------------------------------------------------------------

    @staticmethod
    def lt(d1: datetime, d2: datetime) -> bool:
        """Test if the first datetime is before the second datetime.

        :param d1: (datetime) Datetime to compare.
        :param d2: (datetime) Datetime to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        DatetimeComparator._check_date(d1)
        DatetimeComparator._check_date(d2)
        if type(d1) is type(d2):
            return d1 < d2
        else:
            raise TypeError(DatetimeComparator._ERROR_TYPES_MISMATCH.format(type(d1), type(d2)))

    # -----------------------------------------------------------------------

    @staticmethod
    def le(d1: datetime, d2: datetime) -> bool:
        """Test if the first datetime is before or equal to the second datetime.

        :param d1: (datetime) Datetime to compare.
        :param d2: (datetime) Datetime to be compared with.
        :return: (bool)
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types

        """
        DatetimeComparator._check_date(d1)
        DatetimeComparator._check_date(d2)
        if type(d1) is type(d2):
            return d1 <= d2
        else:
            raise TypeError(DatetimeComparator._ERROR_TYPES_MISMATCH.format(type(d1), type(d2)))

    # -----------------------------------------------------------------------

    @staticmethod
    def gt(d1: datetime, d2: datetime) -> bool:
        """Test if the first datetime is after the second datetime.

        :param d1: (datetime) Datetime to compare.
        :param d2: (datetime) Datetime to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        DatetimeComparator._check_date(d1)
        DatetimeComparator._check_date(d2)
        if type(d1) is type(d2):
            return d1 > d2
        else:
            raise TypeError(DatetimeComparator._ERROR_TYPES_MISMATCH.format(type(d1), type(d2)))

    # -----------------------------------------------------------------------

    @staticmethod
    def ge(d1: datetime, d2: datetime) -> bool:
        """Test if the first datetime is after or equal to the second datetime.

        :param d1: (datetime) Datetime to compare.
        :param d2: (datetime) Datetime to be compared with.
        :raises: TypeError: invalid given parameter.
        :raises: TypeError: Inconsistent types
        :return: (bool)

        """
        DatetimeComparator._check_date(d1)
        DatetimeComparator._check_date(d2)
        if type(d1) is type(d2):
            return d1 >= d2
        else:
            raise TypeError(DatetimeComparator._ERROR_TYPES_MISMATCH.format(type(d1), type(d2)))
