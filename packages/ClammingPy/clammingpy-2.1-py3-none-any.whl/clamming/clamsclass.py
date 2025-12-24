"""
:filename: clamming.clamsclass.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Convert a parsed class object into Markdown or HTML content.

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

import logging

from .claminfo import ClamInfo
from .clamutils import ClamUtils
from .classparser import ClammingClassParser
from .claminfomd import ClamInfoMarkdown

# ---------------------------------------------------------------------------


class ClamsClass:
    """Convert a parsed class object into Markdown or HTML content.

    :example:
    >>> clamming = ClammingClassParser(Vehicle)
    >>> clams = ClamsClass(clamming)
    >>> md = clams.markdown()

    """

    def __init__(self, parsed_obj: ClammingClassParser):
        """Create documentation from the given parsed class object.

        HTML conversion depends on external libraries. It could be disabled
        if any of them is missing. If not, customizing the HTML export can
        be done by assigning different values to members or by changing their
        optional parameters.

        See `Pygments` documentation:
        [HtmlFormatter](https://pygments.org/docs/formatters/#HtmlFormatter)
        and
        [Lexer](https://pygments.org/docs/lexers/#pygments.lexers.python.PythonLexer)

        :example:
        >>> self.markdowner = markdown2.Markdown()
        >>> self.formatter = pygments_formatter.HtmlFormatter(**ClamsClass.HTML_FORMATTER_ARGS)
        >>> self.lexer = pygments_lexers.PythonLexer()

        :param parsed_obj: A parsed object.

        """
        self.__utils = ClamUtils()

        # Grabbed information about the class itself: name and docstring.
        self.__info_class_name = parsed_obj.get_obj_clams().name
        self.__info_class_description = parsed_obj.get_obj_clams()
        self.__info_short_description = self.__info_class_name + ". "
        if self.__info_class_description.docstring is not None:
            lines = self.__info_class_description.docstring.split("\n")
            self.__info_short_description += lines[0]

        # Grabbed information about the class constructor: name, args, source
        # and docstring. They have empty values if the class has no constructor.
        self.__info_constructor = parsed_obj.init_clams

        # Grabbed information about the class functions: name, args, source
        # and docstring. To increase documentation readability, they are
        # categorized as: public, private, protected or overloads.

        self.__info_public_fcts = list()
        for fct_name in parsed_obj.fct_clams:
            if fct_name.startswith("_") is False:
                self.__info_public_fcts.append(parsed_obj.fct_clams[fct_name])

        self.__info_private_fcts = list()
        for fct_name in parsed_obj.fct_clams:
            if fct_name.startswith("_") is True and fct_name.startswith("__") is False:
                self.__info_private_fcts.append(parsed_obj.fct_clams[fct_name])

        self.__info_protected_fcts = list()
        for fct_name in parsed_obj.fct_clams:
            if fct_name.startswith("__") is True and fct_name.endswith("__") is False:
                self.__info_protected_fcts.append(parsed_obj.fct_clams[fct_name])

        self.__info_overloads = list()
        for fct_name in parsed_obj.fct_clams:
            if fct_name.startswith("__") is True and fct_name.endswith("__") is True:
                self.__info_overloads.append(parsed_obj.fct_clams[fct_name])

    # -----------------------------------------------------------------------

    def get_name(self) -> str:
        """Return the name of the documented class."""
        return self.__info_class_name

    name = property(get_name, None)

    # -----------------------------------------------------------------------

    def get_short_description(self) -> str:
        """Return the 160 chars max description of the documented class."""
        return self.__info_short_description

    short_description = property(get_short_description, None)

    # -----------------------------------------------------------------------

    def markdown(self) -> str:
        """Get Markdown content of the parsed object.

        :return: (str) Content in Markdown format

        """
        md = list()
        md.append("## Class `{:s}`\n".format(self.__info_class_name))

        if self.__info_class_description.docstring is not None:
            # Turn only docstring into markdown and append to the result
            md.append("### Description\n")
            md.append(ClamInfoMarkdown.convert_docstring(self.__info_class_description.docstring))
            md.append("\n")

        if len(self.__info_constructor.name) > 0:
            md.append("### Constructor\n")
            md.append(str(ClamInfoMarkdown(self.__info_constructor)))
            md.append("\n")

        if len(self.__info_public_fcts) > 0:
            md.append("### Public functions\n")
            for info in self.__info_public_fcts:
                md.append(str(ClamInfoMarkdown(info)))
            md.append("\n")

        if len(self.__info_private_fcts) > 0:
            md.append("### Private functions\n")
            for info in self.__info_private_fcts:
                md.append(str(ClamInfoMarkdown(info)))
            md.append("\n")

        if len(self.__info_protected_fcts) > 0:
            md.append("### Protected functions\n")
            for info in self.__info_protected_fcts:
                md.append(str(ClamInfoMarkdown(info)))
            md.append("\n")

        if len(self.__info_overloads) > 0:
            md.append("### Overloads\n")
            for info in self.__info_overloads:
                md.append(str(ClamInfoMarkdown(info)))
            md.append("\n")

        return "\n".join(md)

    # -----------------------------------------------------------------------

    def html(self) -> str:
        """Get HTML content of the parsed object.

        :return: (str) Content in HTML format
        :raises: ImportError: if one of the requirements is not installed

        """
        # Can we export to HTML?
        if self.__utils.markdowner is None:
            logging.warning("Markdown to HTML conversion is disabled.")
            return ""

        hd = list()
        cid = self.__info_class_name
        hd.append('<section id="#{:s}">'.format(cid))
        hd.append('<h2>Class {:s}</h2>\n'.format(self.__info_class_name))

        if self.__info_class_description.docstring is not None:
            hd.append("<section>")
            hd.append('<h3 id="#description_{:s}">Description</h3>'.format(cid))
            _html = self.__docstring_to_html(self.__info_class_description.docstring)
            hd.append(ClamsClass._docstring_article(_html))
            hd.append("</section>")

        if len(self.__info_constructor.name) > 0:
            hd.append("<section>")
            hd.append('<h3 id="#constructor_{:s}">Constructor</h3>'.format(cid))
            _html = self.__claminfo_to_html(self.__info_constructor, with_name=False)
            hd.append(_html)
            hd.append("</section>")

        if len(self.__info_public_fcts) > 0:
            hd.append("<section>")
            hd.append('<h3 id="#public_fct_{:s}">Public functions</h3>'.format(cid))
            for info in self.__info_public_fcts:
                hd.append(self.__claminfo_to_html(info))
            hd.append("</section>")

        if len(self.__info_private_fcts) > 0:
            hd.append("<section>")
            hd.append('<h3 id="#private_fct_{:s}">Private functions</h3>'.format(cid))
            for info in self.__info_private_fcts:
                hd.append(self.__claminfo_to_html(info))
            hd.append("</section>")

        if len(self.__info_protected_fcts) > 0:
            hd.append("<section>")
            hd.append('<h3 id="#protected_fct_{:s}">Protected functions</h3>'.format(cid))
            for info in self.__info_protected_fcts:
                hd.append(self.__claminfo_to_html(info))
            hd.append("</section>")

        if len(self.__info_overloads) > 0:
            hd.append("<section>")
            hd.append('<h3 id="#overloads_{:s}">Overloads</h3>'.format(cid))
            for info in self.__info_overloads:
                hd.append(self.__claminfo_to_html(info))
            hd.append("</section>")

        hd.append('</section>')

        html_result = "\n".join(hd)
        return html_result.replace("<p></p>", "")

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    def __docstring_to_html(self, docstring: str) -> str:
        """Return the HTML of the given docstring.

        :param docstring: (str)
        :return: (str) HTML

        """
        _md = ClamInfoMarkdown.convert_docstring(docstring)
        return self.__utils.markdown_to_html(_md)

    # -----------------------------------------------------------------------

    def __claminfo_to_html(self, claminfo: ClamInfo, with_name=True) -> str:
        """Return the HTML of the given ClamInfo instance.

        :return: (str) HTML

        """
        h = list()
        # Name of the class
        if with_name is True:
            h.append("<h4>{:s}</h4>\n".format(claminfo.name))

        # Manage arguments
        params = [p for p in claminfo.args]
        if "self" in params:
            params.remove("self")

        # Docstring: operated by markdown2, and pygments if example
        if claminfo.docstring is not None:
            _html = self.__docstring_to_html(claminfo.docstring)
            # Force arguments to be in a Parameters section
            if len(params) > 0 and "<h5>Parameters</h5>" not in _html:
                _md = "\n\n##### Parameters\n"
                _md += "\n".join(["- **{:s}**".format(p) for p in params])
                _html += self.__utils.markdown_convert(_md)
            h.append(ClamsClass._docstring_article(_html))
            h.append("\n")

        # Source code: operated by pygments
        if len(claminfo.source) > 0:
            _html = ClamUtils().source_to_html(claminfo.source)
            h.append(ClamsClass._source_accordion("View Source", _html))
        h.append("\n")

        html_result = "\n".join(h)
        return html_result.replace("<p></p>", "")

# ---------------------------------------------------------------------------

    @staticmethod
    def _source_accordion(header_content: str, main_content: str) -> str:
        """Return the given content embedded into a details element.

        :param header_content: (str) Content of the collapsed part
        :param main_content: (str) Content of the expanded part
        :return: (str) HTML-5 of an article

        """
        h = list()
        h.append('    <details>')
        h.append('    <summary>')
        h.append(header_content)
        h.append('    </summary>')
        h.append(main_content)
        h.append('    </details>')
        return "\n".join(h)

# ---------------------------------------------------------------------------

    @staticmethod
    def _docstring_article(content: str) -> str:
        """Return the given content embedded into an article.

        :param content: Content of the article
        :return: (str) HTML-5 of an article

        """
        h = list()
        h.append('    <article class="docstring">')
        h.append(content)
        h.append('    </article>')
        html_result = "\n".join(h)
        return html_result.replace("<p></p>", "")
