"""
:filename: clamming.claminfomd.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Convert and store ClamInfo data into Markdown format.

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

import builtins

from .claminfo import ClamInfo

# ---------------------------------------------------------------------------


class ClamInfoMarkdown:
    """Convert and store ClamInfo data into Markdown format.

    Docstrings are analyzed with **flexibility rather than completeness...
    it's the choice here.**

    > Both ReST and Epydoc field styles are supported. :field: or @field: can be used indifferently, with upper- or lower- cases.

    Two very useful non-standard field list are added:
    `:example:` and `:code:`

    Finally, some variants in field names are supported:

        - :return: or :returns: are both interpreted the same way;
        - :raise: or :raises: or :catch: or :except: are all interpreted the same way.

    """

    # Matching variants in writing the field. Key=variant, value=field
    VARIANT_FIELDS = dict()
    VARIANT_FIELDS["returns"] = "return"
    VARIANT_FIELDS["raises"] = "raise"
    VARIANT_FIELDS["catch"] = "raise"
    VARIANT_FIELDS["except"] = "raise"
    VARIANT_FIELDS["code"] = "example"

    # Field list representing a Markdown section. Multiline is supported.
    MARKDOWN_SECTION = dict()
    MARKDOWN_SECTION["param"] = "##### Parameters\n"
    MARKDOWN_SECTION["return"] = "##### Returns\n"
    MARKDOWN_SECTION["raise"] = "##### Raises\n"
    MARKDOWN_SECTION["example"] = "##### Example\n"

    # `type` and `rtype` are ignored. It is expected that the source code
    # is using modern type annotations.
    IGNORE_FIELDS = ["type", "rtype"]

    # Python types
    PY_TYPES = [getattr(builtins, d).__name__ for d in dir(builtins) if isinstance(getattr(builtins, d), type)]

    # -----------------------------------------------------------------------

    def __init__(self, clam: ClamInfo):
        """Create a ClamInfoMarkdown converter.

        :param clam: (ClamInfo)
        :raises: TypeError: The given argument is not a ClamInfo.

        """
        if isinstance(clam, ClamInfo) is False:
            raise TypeError("Expected a 'ClamInfo' for the ClamInfoMarkdown.clam, got {:s} instead."
                            "".format(str(type(clam))))
        self.__clam = clam

    # -----------------------------------------------------------------------
    # Get access to ClamInfo members
    # -----------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Return the name into Markdown format."""
        return self.convert_name(self.__clam.name)
    
    @property
    def args(self) -> list:
        """Return the list of arguments."""
        return self.__clam.args
    
    @property
    def source(self) -> str:
        """Return the source code in Markdown format."""
        return self.convert_source(self.__clam.source)
    
    @property
    def docstring(self) -> str:
        """Return the docstring in Markdown format."""
        return self.convert_docstring(self.__clam.docstring)
    
    # -----------------------------------------------------------------------
    # Convert a ClamInfo member into Markdown format
    # -----------------------------------------------------------------------

    @staticmethod
    def convert_name(name: str) -> str:
        """Convert the given name into markdown.

        :param name: (str) Name of a function or class
        :return: (str) The name in Markdown

        """
        return "#### {:s}".format(str(name))

    # -----------------------------------------------------------------------

    @staticmethod
    def convert_source(source: str) -> str:
        """Convert source code into markdown.

        :param source: (str) Source code of a function or class or anything
        :return: (str) The source in Markdown

        """
        source = str(source)
        if len(source) == 0:
            return ""

        code = list()
        code.append("\n```python")
        code.append(source)
        code.append("```\n")
        return "\n".join(code)

    # -----------------------------------------------------------------------

    @staticmethod
    def convert_docstring(docstring: str) -> str:
        """Convert reStructuredText of a docstring to Markdown.

        :param docstring: (str) The docstring of any source code.
        :return: (str) Docstring in Markdown.

        """
        if docstring is None:
            return ""
        md = list()
        is_field_section = ""
        for i, line in enumerate(docstring.split("\n")):
            text = line.strip()
            if len(text) == 0:
                is_field_section = ""

            if i == 0 and text.endswith("."):
                # The first line is the short description of a function.
                md.append("*{:s}*".format(text))

            # A reST or Epydoc field that will be a markdown section?
            elif text.startswith(":") or text.startswith("@"):
                fieldname, text = ClamInfoMarkdown._extract_fieldname(text)
                # A known field list. New section list.
                if fieldname is not None:
                    if is_field_section != fieldname:
                        if len(is_field_section) > 0:
                            # End of a previous field section
                            md.append("\n")
                        # Start of a new section
                        md.append(ClamInfoMarkdown.MARKDOWN_SECTION[fieldname])
                    is_field_section = fieldname

                    if len(text) > 0:
                        if fieldname == "param":
                            md.append(ClamInfoMarkdown._param(text))
                        elif fieldname in ("raise", "raises"):
                            md.append(ClamInfoMarkdown._raise(text))
                        elif fieldname in ("return", "returns"):
                            md.append(ClamInfoMarkdown._return(text))
                        elif fieldname == "example":
                            md.append(ClamInfoMarkdown._example(text))
                        elif fieldname is not None and len(text) > 0:
                            # hum... we should never be here.
                            md.append(text)
                else:
                    if len(text) > 0:
                        # A field used like a description list item.
                        md.append(ClamInfoMarkdown._plist(text))
                        is_field_section = ""

            elif text.startswith(">>>"):
                # if ":example:" was missing before the source code
                if is_field_section != "example":
                    # End of the previous section
                    md.append("\n")
                    # Start of the example
                    md.append(ClamInfoMarkdown.MARKDOWN_SECTION["example"])
                is_field_section = "example"
                md.append(ClamInfoMarkdown._example(text))

            elif len(is_field_section) > 0 and len(md) > 0:
                # A line of the current field as a new entry
                if is_field_section == "example":
                    md.append(ClamInfoMarkdown._example(text))
                else:
                    # A continued line of the current field (param, raise or return)
                    md[-1] = "{:s} {:s}".format(md[-1], text)
            else:
                md.append(text)

        return "\n".join(md)

    # -----------------------------------------------------------------------
    # Private function to analyze and convert a docstring
    # -----------------------------------------------------------------------

    @staticmethod
    def _extract_fieldname(text: str) -> (str, str):
        """Extract a supposed field name from the given text.

         Text field can be of type `@field:` (epydoc) or `:field:` (reST).

         Some examples of supported input text and the returned tuple:

         - "@param name: THE name" returns ("name", "THE name")
         - :param name: THE name" returns ("name", "THE name")
         - ":example:" returns ("example", "")
         - ":return: Something" returns ("return", "Something")
         - "Something here" returns (None, "Something here")

        :param text: (str) Any line of text starting by a field.
        :return: (field_name, description)

        """
        if len(text) == 0:
            return None, ""
        if text[0] not in ("@", ":"):
            return None, text

        try:
            # for lines like: ":param x:", whitespace is before ":"
            sep_whitespace = text.index(" ")
        except ValueError:
            sep_whitespace = len(text)
        try:
            # for lines like: ":return: x", ":" are before whitespace
            sep_dots = text[1:].index(":")
        except ValueError:
            sep_dots = len(text)

        pos = min(sep_whitespace, sep_dots)
        if pos < len(text):
            field_name = ClamInfoMarkdown._fieldname_variant(text[1:pos+1])
            if field_name in ClamInfoMarkdown.IGNORE_FIELDS:
                # Ignore the full line.
                return None, ""

            if pos == sep_whitespace:
                content = text[pos+1:].strip()
            else:
                content = text[pos+2:].strip()

            if field_name in ClamInfoMarkdown.MARKDOWN_SECTION.keys():
                return field_name, content

        return None, text

    # -----------------------------------------------------------------------

    @staticmethod
    def _fieldname_variant(name: str) -> str:
        """Return the corresponding normalized field.

        Some examples of supported input text and the returned string:

        - "return" returns "return"
        - "Returns" returns "return"
        - "ANYTHING returns "anything"

        :param name: (str) A supposed field-name or one of the variants
        :return: (str) normalized field

        """
        # Normalize the name
        name = name.lower().strip()
        # if one of the variant, return the field
        if name in ClamInfoMarkdown.VARIANT_FIELDS:
            return ClamInfoMarkdown.VARIANT_FIELDS[name]
        return name

    # -----------------------------------------------------------------------

    @staticmethod
    def _ptype(text: str) -> str:
        """Surround an indicated python type with *".

        Some examples of supported input text and the returned string:

        - "(str)" returns "(*str*)"
        - "(str,int)" returns "(*str*,*int*)"
        - "list(str)" returns "list(*str*)"
        - "(list[str])" returns "(*list*[*str*])"
        - "(any)" returns "(any)"
        - "some text" returns "some text"
        - " (some text) " returns "(some text)"

        :param text: (str) Text to be analyzed to emphasize python types
        :return: (str) analyzed text

        """
        text = text.strip()
        if "(" in text and ")" in text:
            b = text.index("(")
            e = text.index(")")
            if e > b:
                parenthesis = text[b:e].strip()
                for py_type in ClamInfoMarkdown.PY_TYPES:
                    if py_type in parenthesis:
                        parenthesis = parenthesis.replace(py_type, "*{:s}*".format(py_type))
                return "{:s}{:s}{:s}".format(text[:b].strip(), parenthesis.strip(), text[e:].strip())
        return text

    # -----------------------------------------------------------------------

    @staticmethod
    def _param(text: str) -> str:
        """Make param text a list item and surround the param name with '**'.

         Some examples of supported input text and the returned string:

         - "name: THE name" returns "- **name**: THE name"
         - "name: (str) THE name" returns "- **name**: (*str*) THE name"
         - "name: (str|int) THE name" returns "- **name**: (*str*|*int*) THE name"
         - "THE name" returns "THE name"

        :param text: (str) Any line of text that started by a param field.
        :return: analyzed text with surrounded field

        """
        text = text.strip()
        if len(text) == 0:
            return ""

        if ":" in text:
            sep_dots = text.index(":")
            param_name = text[:sep_dots].strip()
            param_descr = text[sep_dots+1:].strip()
            if len(param_descr) > 0:
                return "- **{:s}**: {:s}".format(param_name, ClamInfoMarkdown._ptype(param_descr))
            else:
                return "- **{:s}**".format(param_name)

        return ClamInfoMarkdown._ptype(text)

    # -----------------------------------------------------------------------

    @staticmethod
    def _raise(text: str) -> str:
        """Make raise text a list item.

        Some examples of supported input text and the returned string:

         - "THE error" returns "- THE error"
         - "ValueError: THE problem" returns "- **ValueError**: THE problem"

        :param text: (str) Any line of text that started by a raise field.
        :return: analyzed text with surrounded exception name

        """
        text = text.strip()
        if len(text) == 0:
            return ""

        if ":" in text:
            # In case the exception name was given
            sep_dots = text.index(":")
            raise_tag = text[:sep_dots].strip()
            raise_descr = text[sep_dots+1:].strip()
            if len(raise_descr) > 0:
                return "- *{:s}*: {:s}".format(raise_tag, raise_descr)
            else:
                return "- *{:s}*".format(raise_tag)

        return text

    # -----------------------------------------------------------------------

    @staticmethod
    def _return(text: str) -> str:
        """Make return text a list item.

        Some examples of supported input text and the returned string:

         - "THE name" returns "- THE name"
         - "(str|int) THE name" returns "- (*str*|*int*) THE name"
         - "tag: THE name" returns "- **tag**: THE name"
         - "tag:" returns "- **tag**"

        :param text: (str) Any line of text that started by a return field.
        :return: analyzed text with surrounded tag

        """
        text = text.strip()
        if len(text) == 0:
            return ""

        if ":" in text:
            # In case a "tag" was given to the returned entity
            sep_dots = text.index(":")
            return_tag = text[:sep_dots].strip()
            return_descr = text[sep_dots+1:].strip()
            if len(return_descr) > 0:
                return "- **{:s}**: {:s}".format(return_tag, ClamInfoMarkdown._ptype(return_descr))
            else:
                return "- **{:s}**".format(return_tag)

        return "- {:s}".format(ClamInfoMarkdown._ptype(text))

    # -----------------------------------------------------------------------

    @staticmethod
    def _example(text: str) -> str:
        """Make example text a >>> item.

        Some examples of supported input text and the returned string:

         - ">>>print('Hello')" returns "    >>> print('Hello')"
         - "print('Hello')" returns "    >>> print('Hello')"

        :param text: (str) Any line of code in an example section.
        :return: analyzed text with ">>>" pre-pended

        """
        text = text.strip()
        if text.startswith(">>>"):
            code = text[3:].strip()
            return "    >>> {:s}".format(code)
        else:
            return "    > {:s}".format(text)

    # -----------------------------------------------------------------------

    @staticmethod
    def _plist(text: str) -> str:
        """Turn an indicated field list into a list item.

        Some examples of supported input text and the returned string:

         - ":Author: someone" returns "- **Author**: someone"
         - ":Author: " returns "- **Author**"
         - "Author: no " returns "Author: no"

        :param text: (str) Any line of text that started by any field.
        :return: analyzed text with surrounded field

        """
        text = str(text)
        text = text.strip()
        if len(text) < 3:
            return text

        if text.startswith(":") and ":" in text[1:]:
            e = text[1:].index(":") + 1
            item = text[1:e].strip()
            descr = text[e+1:].strip()
            if len(descr) > 0:
                return "- **{:s}**: {:s}".format(item, descr)
            else:
                return "- **{:s}**".format(item)
        else:
            return text

    # -----------------------------------------------------------------------
    # Overloads
    # -----------------------------------------------------------------------

    def __str__(self):
        return "{:s}\n{:s}\n{:s}\n".format(self.name, self.source, self.docstring)
