"""
:filename: clamming.claminfo.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Data class to store information about a clam.

.. _This file is part of ClammingPy: https://clamming.sourceforge.io
..
    -------------------------------------------------------------------------

    Copyright (C) 2023-2025 Brigitte Bigi, CNRS
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
from typing import NoReturn

# -----------------------------------------------------------------------


class ClamInfo:
    """The information extracted for a function in the documented class.

    Public members are:

    - name (str): required, the name of the function
    - args (list of str): optional, the arguments of the function
    - source (str): optional, the source code of the function, including its definition
    - docstring (str or None): optional, the docstring of the function

    :example:
    >>> clam_info = ClamInfo("add", args=tuple("a", "b"), source="def add(a, b): return a+b", docstring="Add two args.")
    >>> clam_info.name
    add
    >>> clam_info.args
    ["a", "b"]
    >>> clam_info.source
    "def add(a, b): return a+b"
    >>> clam_info.docstring
    "Add two args."
    >>> clam_info = ClamInfo("add", args=tuple("a", "b"), source="def add(a, b): return a+b")
    >>> clam_info.docstring
    None

    :raises: TypeError: if a given argument is not of the expected type.

    """

    def __init__(self,  name: str,
                 args: list[str] | tuple[str] = (),
                 source: str = "",
                 docstring: str | None = None):
        """Create a data class for a documented function.

        :param name: (str) Name of the documented function
        :param args: (list|tuple) List of its arguments
        :param source: (str) Source code of the function
        :param docstring: (str) Docstring of the function
        :raises: TypeError: Wrong type of one of the given parameters

        """
        self.__name = ""
        self.__args = list()
        self.__source = ""
        self.__docstring = None

        self.set_name(name)
        self.set_args(args)
        self.set_source(source)
        self.set_docstring(docstring)

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the stored class."""
        return self.__name

    def set_name(self, name: str) -> NoReturn:
        """Set a new name.

        :param name: (str) New name of the documented function/class/...
        :raises: TypeError: given class_name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the ClamInfo.name, got {:s} instead."
                            "".format(str(type(name))))
        self.__name = name

    name = property(get_name, set_name)

    # -----------------------------------------------------------------------

    def get_args(self) -> list:
        """Return a copy of the list of arguments."""
        return [i for i in self.__args]

    def set_args(self, args: list[str] | tuple[str]) -> NoReturn:
        """Set the list of args.

        :param args: (list|tuple) Source code
        :raises: TypeError: The given args is not a list or tuple

        """
        if isinstance(args, (list, tuple)) is False:
            raise TypeError("Expected a 'list' or 'tuple' for the ClamInfo.args. Got {:s} instead."
                            "".format(str(type(args))))
        self.__args = args

    args = property(get_args, set_args)

    # -----------------------------------------------------------------------

    def get_source(self) -> str:
        """Return the source code."""
        return self.__source

    def set_source(self, source: str) -> NoReturn:
        """Set a new source code.

        :param source: (str) Source code
        :raises: TypeError: The given source code is not a string

        """
        if isinstance(source, str) is False:
            raise TypeError("Expected a 'str' for the ClamInfo.source, got {:s} instead."
                            "".format(str(type(source))))
        self.__source = source

    source = property(get_source, set_source)

    # -----------------------------------------------------------------------

    def get_docstring(self) -> str:
        """Return the docstring of the class."""
        return self.__docstring

    def set_docstring(self, docstring: str) -> NoReturn:
        """Set a new docstring to the class."""
        if docstring is not None:
            if isinstance(docstring, str) is False:
                raise TypeError("Expected a 'str' for the ClamInfo.docstring. Got {:s} instead."
                                "".format(str(type(docstring))))
        self.__docstring = docstring

    docstring = property(get_docstring, set_docstring)
