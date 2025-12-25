# -*- coding: UTF-8 -*-
"""
:filename: whakerkit.config.typesmapping.py
:author: Brigitte Bigi
:contributor: Chiheb Bradai
:contact: contact@sppas.org
:summary: Map the types and how to convert them.

.. _This file is part of WhakerKit: https://whakerkit.sourceforge.io
.. _This file was originally part of WhintPy - by Brigitte Bigi, CNRS.
    Integrated into WhakerKit as of 2025-05-23.

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
from datetime import datetime

# ---------------------------------------------------------------------------


class TypesMapping:
    """Map the types and how to convert them.

    It is used by `TypeDealer.cast_types` to cast the types. It allows to
    add types and how to convert them in the `TypesMapping` class.

    """

    def __init__(self):
        """Initialize the type mapping with the default date format.

        """
        self.__dict__ = dict(
            int=int,
            str=str,
            bool=lambda x: x.lower() == 'true' if isinstance(x, str) else bool(x),
            float=float,
            list=lambda x: [elm for elm in x] if isinstance(x, str) else [int(elm) for elm in str(x)],
            dict=lambda x: {elm: elm for elm in x} if isinstance(x, str) else {elm: int(elm) for elm in str(x)},
            tuple=lambda x: tuple(elm for elm in x) if isinstance(x, str) else (int(elm) for elm in x),
            datetime=lambda x, fmt='%Y-%m-%d': datetime.strptime(x, fmt).strftime(fmt),
            date=lambda x, fmt='%Y-%m-%d': datetime.strptime(x, fmt).date().strftime(fmt)
        )

    # -----------------------------------------------------------------------

    def get_type(self, type_name: type | str, date_format: str | None = None):
        """Get the conversion function for the given type name.

        :param type_name: The name of the type
        :param date_format: The date format
        :raises: TypeError: if the type_name is not a string
        :return: The conversion function or None if the type is not found

        """
        from .typesdealer import TypesDealer
        TypesDealer.check_types("TypeMapping.get_type", [(type_name, (type, str)), (date_format, (str, type(None)))])
        if type_name in ['datetime', 'date'] and date_format is not None:
            return lambda x: self.__dict__[type_name](x, date_format)
        if type_name in self.__dict__:
            return self.__dict__[type_name]
        return None

    # -----------------------------------------------------------------------

    def add_conversion(self, type_name: str | type, conversion_function):
        """Add a conversion function to the type mapping.

        :param type_name: The name of the type
        :param conversion_function: The conversion function
        :raises: TypeError: if the type_name is not a string or the conversion_function is not callable

        """
        # TO DO: find another solution because typesmapping imports typesdealer and VICE-VERSA.
        # so there's a problem in the program logic.
        from .typesdealer import TypesDealer
        if conversion_function is None:
            raise TypeError("TypeMapping.add_conversion 'conversion_function' cannot be None.")
        if conversion_function == "":
            raise TypeError("TypeMapping.add_conversion 'conversion_function' cannot be an empty string.")

        TypesDealer.check_types("TypeMapping.add_conversion", [(type_name, (type, str)), ])
        self.__dict__[type_name] = conversion_function
