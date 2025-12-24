"""
:filename: clamming.clamspack.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Create documentation of a module into Markdown or HTML.

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
import inspect
import codecs
import os
import logging
from typing import Any
try:
    import markdown2
    HTML = ""
except ImportError as e:
    HTML = str(e)

import clamming
from clamming.clamsclass import ClamsClass
from clamming.classparser import ClammingClassParser
from clamming.exportoptions import ExportOptions
from clamming.clamutils import ClamUtils

# ---------------------------------------------------------------------------


class ClamsPack:
    """Create documentation of a module into Markdown or HTML.

    :example:
    >>> clams = ClamsPack(clamming)
    >>> md = clams.markdown()

    """

    def __init__(self, pack: Any):
        """Create documentation from the given package name.

        :param pack: (module) A Python module
        :raises: TypeError: given 'pack' is not a module

        """
        if inspect.ismodule(pack) is False:
            raise TypeError("Expected a Python module. Got {:s} instead.".format(str(pack)))

        self.__pack = pack
        self.__clams = list()
        try:
            for class_name in pack.__all__:
                # Turn class_name into an instance name
                class_inst = ClamUtils.get_class(class_name, self.__pack.__name__)
                if class_inst is not None:
                    # Parse the object and store collected information = clamming
                    clammer = ClammingClassParser(class_inst)
                    # Store the collected clams
                    self.__clams.append(ClamsClass(clammer))
        except AttributeError:
            logging.warning("Attribute __all__ is missing in package {:s} => No auto documentation."
                            "".format(self.__pack.__name__))

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the package."""
        return self.__pack.__name__

    name = property(get_name, None)

    # -----------------------------------------------------------------------

    def get_readme(self) -> str:
        """Return the content of the README file of the package, if any."""
        path_to_readme = os.path.dirname(self.__pack.__file__)
        readme_content = ""
        for f in os.listdir(path_to_readme):
            if "readme" in f.lower():
                readme_file = os.path.join(path_to_readme, f)
                try:
                    with open(readme_file, "r", encoding="utf-8") as f:
                        readme_content = f.read()
                except Exception as e:
                    logging.warning("A README file was found but could not be read: {:s}".format(str(e)))
                break

        return readme_content

    readme = property(get_readme, None)

    # -----------------------------------------------------------------------

    def markdown(self, exporter: ExportOptions | None = None) -> str:
        """Return the documentation of the package as a standalone Markdown content.

        """
        md = list()
        md.append("# {:s} module\n".format(self.name))

        # Module README content - if any
        if exporter is not None:
            if exporter.readme is True and len(HTML) == 0:
                readme_content = self.get_readme()
                if len(readme_content) > 0:
                    md.append(readme_content)

        # Classes
        md.append("## List of classes\n")

        for clams in self.__clams:
            md.append(clams.markdown())
        md.append("\n\n~ Created using [Clamming](https://clamming.sf.net) version {:s} ~\n"
                  "".format(clamming.__version__))

        return "\n".join(md)

    # -----------------------------------------------------------------------

    def html(self, exporter: ExportOptions | None = None) -> str:
        """Return the documentation of the package as an HTML content."""
        html = list()
        html.append("<h1>{:s} module</h1>\n".format(self.name))

        # Module README content - if any
        if exporter is not None:
            if exporter.readme is True and len(HTML) == 0:
                readme_content = self.get_readme()
                if len(readme_content) > 0:
                    html.append("    <section id=\"readme\">\n")
                    html.append(ClamUtils().markdown_to_html(readme_content))
                    html.append("    </section>\n")

        html.append("<h2>List of classes</h2>\n")
        for clams in self.__clams:
            html.append(clams.html())
        html.append("\n\n<p>~ Created using <a href=\"https://clamming.sf.net\">ClammingPy</a> version {:s} ~</p>\n"
                    "".format(clamming.__version__))

        return "\n".join(html)

    # -----------------------------------------------------------------------

    def html_index(self,
                   path_name: str | None = None,
                   exporter: ExportOptions | None = None) -> str:
        """Create the HTML content of an index for the package.

        :param path_name: (str) Path where the exported HTML files are, or None for a standalone content.
        :param exporter: (HTMLDocExport) Options for HTML output files
        :return: (str) HTML code

        """
        out = list()
        out.append("    <section id=\"#{:s}\">".format(self.name))
        out.append("    <h1>{:s} module</h1>".format(self.name))

        # Module README content - if any
        if exporter is not None:
            if exporter.readme is True and len(HTML) == 0:
                readme_content = self.get_readme()
                if len(readme_content) > 0:
                    out.append("    <section id=\"readme\">\n")
                    out.append(ClamUtils().markdown_to_html(readme_content))
                    out.append("    </section>\n")

        out.append("<h2>List of classes</h2>\n")
        out.append('        <section class="cards-panel">')
        for i in range(len(self.__clams)):
            clams = self.__clams[i]
            out.append('        <article class="card">')
            out.append('            <header><span>{:d}</span></header>'.format(i + 1))
            out.append('            <main>')
            out.append('                <h3>{:s}</h3>'.format(clams.name))
            out.append('            </main>')
            out.append('            <footer>')
            if path_name is not None:
                # External link
                out.append('                <a role="button" href="{:s}">Read me →</a>'
                           ''.format(os.path.join(path_name, clams.name + ".html")))
            else:
                # Local link
                out.append('                <a role="button" href="#{:s}">Read me →</a>'
                           ''.format(clams.name))
            out.append('            </footer>')
            out.append('        </article>')

        out.append("        </section>")
        out.append("    </section>")

        return "\n".join(out)

    # -----------------------------------------------------------------------

    def html_export_clams(self, path_name: str, exporter: ExportOptions) -> list[str]:
        """Create the HTML pages of all classes of the package.

        :param path_name: (str) Path where to add the exported HTML files
        :param exporter: (HTMLDocExport) Options for HTML output files
        :return: (list) Exported file names

        """
        out = list()
        if os.path.exists(path_name) is False:
            os.mkdir(path_name)

        logging.info("Export module index")
        out_html = os.path.join(path_name, self.name + ".html")
        self.__module_index(out_html, exporter)
        out.append(out_html)

        for i in range(len(self.__clams)):
            clams = self.__clams[i]
            out_html = os.path.join(path_name, clams.name + ".html")
            logging.info("Export {:s}".format(out_html))

            exporter.prev_class = None if i == 0 else self.__clams[i - 1].name + ".html"
            exporter.next_class = None if i + 1 == len(self.__clams) else self.__clams[i + 1].name + ".html"
            exporter.description = clams.get_short_description()
            html_content = clams.html()
            self.__module_class(out_html, exporter, html_content)

        return out

    # ---------------------------------------------------------------------------
    # Private
    # ---------------------------------------------------------------------------

    def __module_index(self, out_html, exporter):
        """Export an index for the module.

        """
        # The module file index: links to each class file
        with codecs.open(out_html, "w", "utf-8") as fp:
            fp.write("<!DOCTYPE html>\n")
            fp.write("<html>\n")
            fp.write(exporter.get_head())
            fp.write("<body class=\"{:s}\">\n".format(exporter.get_theme()))
            fp.write("    {:s}\n".format(exporter.get_header()))
            fp.write("    {:s}\n".format(exporter.get_nav()))
            fp.write("    <main id=\"main-content\">\n")
            # Module index: list of classes in the module
            fp.write(self.html_index(path_name="", exporter=exporter))
            fp.write("    </main>\n")
            fp.write("    {:s}\n".format(exporter.get_footer()))
            fp.write("</body>\n")
            fp.write("</html>\n")

    # ---------------------------------------------------------------------------

    def __module_class(self, out_html, exporter, content):
        """Export a content for the module.

        """
        with codecs.open(out_html, "w", "utf-8") as fp:
            fp.write("<!DOCTYPE html>\n")
            fp.write("<html>\n")
            fp.write(exporter.get_head())
            fp.write("<body class=\"{:s}\">\n".format(exporter.get_theme()))
            fp.write("    {:s}\n".format(exporter.get_header()))
            fp.write("    {:s}\n".format(exporter.get_nav()))
            fp.write("    <main id=\"main-content\">\n")
            fp.write("    <section id=\"#{:s}\">".format(self.name))
            fp.write("    <h1>Module {:s}</h1>\n".format(self.name))
            fp.write(content)
            fp.write("    </section>")
            fp.write("    </main>\n")
            fp.write("    {:s}\n".format(exporter.get_footer()))
            fp.write("</body>\n")
            fp.write("</html>\n")

    # ---------------------------------------------------------------------------
    # Overloads
    # ---------------------------------------------------------------------------

    def __len__(self):
        """Return the number of documented pages of the package."""
        return len(self.__clams)
