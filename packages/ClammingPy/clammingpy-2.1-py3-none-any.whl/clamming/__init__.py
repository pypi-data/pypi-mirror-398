"""
:filename: clamming.__init__.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Generate documentation in Markdown or HTML.

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

from .clamutils import ClamUtils
from .claminfo import ClamInfo
from .claminfomd import ClamInfoMarkdown
from .classparser import ClammingClassParser
from .clamsclass import ClamsClass
from .clamspack import ClamsPack
from .clamsmodules import ClamsModules
from .exportoptions import ExportOptions

__author__ = "Brigitte Bigi"
__copyright__ = "Copyright (C) 2023-2025 Brigitte Bigi, CNRS, Laboratoire Parole et Langage, Aix-en-Provence, France"
__version__ = "2.1"
__all__ = (
    "ClamUtils",
    "ClamInfo",
    "ClamInfoMarkdown",
    "ClammingClassParser",
    "ClamsClass",
    "ClamsPack",
    "ClamsModules",
    "ExportOptions"
)
