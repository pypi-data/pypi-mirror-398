"""
:filename: clamming.clamsmodules.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create documentation of a list of modules into Markdown or HTML.

.. _This file is part of ClammingPy: https://clamming.sourceforge.io
..
    -------------------------------------------------------------------------

    Copyright (C) 2023-2025 Brigitte Bigi, CNRS,
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
import os
import logging
import codecs
import traceback

from .exportoptions import ExportOptions
from .clamspack import ClamsPack
from .clamutils import ClamUtils

# ---------------------------------------------------------------------------


class ClamsModules:
    """Create documentation of a list of modules into Markdown or HTML.

    :example:
    >>> clams = ClamsModules(clamming)
    >>> md = clams.markdown()

    """

    def __init__(self, modules: list):
        """Create documentation from the given package name.

        :param modules: list(modules) A list of Python modules
        :raises: TypeError: a given entry is not a module

        """
        if isinstance(modules, list) is False:
            raise TypeError("Expected a list of Python modules. Got {:s} instead.".format(str(modules)))

        self.__clams_packs = list()
        for m in modules:
            self.__clams_packs.append(ClamsPack(m))

    # -----------------------------------------------------------------------
    # Documentation for a list of modules.
    # -----------------------------------------------------------------------

    def markdown_export_packages(self, path_name: str, exporter: ExportOptions) -> list[str]:
        """Create a Markdown file for each of the packages.

        :param path_name: (str) Path where to add the exported md files
        :param exporter: (HTMLDocExport) Options for HTML output files
        :return: (list) Exported file names

        """
        out = list()

        for clams_pack in self.__clams_packs:
            out_md = os.path.join(path_name, clams_pack.name + ".md")
            if os.path.exists(path_name) is False:
                os.mkdir(path_name)

            logging.info("Export {:s}".format(out_md))
            with codecs.open(out_md, "w", "utf-8") as fp:
                fp.write(clams_pack.markdown())
            out.append(out_md)

        return out

    # -----------------------------------------------------------------------

    def html_export_index(self,
                          path_name: str,
                          exporter: ExportOptions,
                          readme: str | None = None) -> str:
        """Write the index.html file from the list of packages.

        :param path_name: (str) Path where to add the exported index.html file
        :param exporter: (HTMLDocExport) Options for HTML output files
        :param readme: (str) A markdown README filename to be added into the index.html
        :return: (str) Filename of the created HTML index file

        """
        logging.info("Export index.html")
        out = os.path.join(path_name, "index.html")
        if os.path.exists(path_name) is False:
            os.mkdir(path_name)

        with codecs.open(out, "w", "utf-8") as fp:
            fp.write("<!DOCTYPE html>\n")
            fp.write("<html>\n")
            fp.write(exporter.get_head())
            fp.write("<body class=\"{:s}\">\n".format(exporter.get_theme()))
            fp.write("    {:s}\n".format(exporter.get_header()))
            fp.write("    {:s}\n".format(exporter.get_nav()))
            fp.write("    <main id=\"main-content\">\n")
            if readme is not None:
                try:
                    with codecs.open(readme, "r", "utf-8") as readme_fp:
                        readme_content = readme_fp.read()
                        if len(readme_content) > 0:
                            fp.write("    <section id=\"readme\">\n")
                            fp.write(ClamUtils().markdown_to_html(readme_content))
                            fp.write("    </section>\n")
                except Exception as e:
                    logging.error(e)
                    traceback.print_exc()

            fp.write("<h1>List of packages:</h1>\n")
            for clams_pack in self.__clams_packs:
                fp.write("      <h2>{:s}</h2>\n".format(clams_pack.name))
                fp.write("      <p><a href='{:s}'>Get documentation</a></p>\n".format(clams_pack.name + ".html"))
            fp.write("    </main>\n")
            fp.write("    {:s}\n".format(exporter.get_footer()))
            fp.write("</body>\n")
            fp.write("</html>\n")
        return out

    # -----------------------------------------------------------------------

    def html_export_packages(self,
                             path_name: str,
                             exporter: ExportOptions,
                             readme: str | None = None) -> list:
        """Create all the HTML files from the list of packages.

        - create the HTML file for each class of each given module;
        - create an index.html file.

        :param path_name: (str) Path where to add the exported index.html file
        :param exporter: (HTMLDocExport) Options for HTML output files
        :param readme: (str) A markdown README filename to be added into the index.html
        :return: (list) Exported file names

        """
        out = list()

        # Create the index.html page. It's a table of content.
        out_index = self.html_export_index(path_name, exporter, readme)
        out.append(out_index)

        # Create an HTML page for each class of each module
        for i in range(len(self.__clams_packs)):
            clams_pack = self.__clams_packs[i]
            exporter.prev_module = None if i == 0 else self.__clams_packs[i - 1].name + ".html"
            exporter.next_module = None if i + 1 == len(self.__clams_packs) else self.__clams_packs[i + 1].name + ".html"
            out_html = clams_pack.html_export_clams(path_name, exporter)
            out.extend(out_html)

        return out
