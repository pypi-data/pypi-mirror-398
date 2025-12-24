"""
:filename: clamming.clamsutils.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Utilities for working with CLAMS data.

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
import importlib
import logging
import sys
from typing import Any
# Libraries in requirements.txt
try:
    from pygments import highlight as pygments_highlight
    from pygments import formatters as pygments_formatter
    from pygments import lexers as pygments_lexers
    import markdown2
    HTML = ""
except ImportError as e:
    HTML = str(e)
    print("ERROR=============>>>>>>>>>>>>"+str(e))

# ---------------------------------------------------------------------------


class ClamUtils:
    """Some utilities for ClammingPy.

    """

    # Keyword arguments of Pygments HtmlFormatter
    HTML_FORMATTER_ARGS = {
        "linenos": False,
        "full": False,
        "nobackground": True,
        "wrapcode": True,
        "style": 'colorful'}

    # ---------------------------------------------------------------------------

    def __init__(self, ):
        """Create a ClamUtils instance."""
        self.markdowner = None
        self.lexer = None
        self.formatter = None

        if len(HTML) == 0:
            # Use markdown2 library to convert docstrings
            self.markdowner = markdown2.Markdown()
            # Use pygments library to convert source code
            # https://pygments.org/docs/formatters/#HtmlFormatter
            self.formatter = pygments_formatter.HtmlFormatter(**ClamUtils.HTML_FORMATTER_ARGS)
            # https://pygments.org/docs/lexers/#pygments.lexers.python.PythonLexer
            self.lexer = pygments_lexers.PythonLexer()

    # ---------------------------------------------------------------------------

    @staticmethod
    def get_class(class_name: str, module_name: str | None = None) -> Any:
        """Return a class object by its name, regardless of import context.

        This method searches for a class within a module, whether the module
        has been imported from a package, from a local test, or executed as
        a script. It first checks already-loaded modules (``sys.modules``),
        then attempts a safe import using ``importlib``.

        This approach ensures stability both for installed packages
        (e.g., ``clamming``) and for local tests (e.g., ``tests.test_clamutils``).

        :param class_name: (str) Name of the class to retrieve.
        :param module_name: (str|None) Name of the module where to look for the class.
                            If None, defaults to the caller’s module.
        :return: (class|None) Class object if found, otherwise None.
        """

        # Default to the caller module if not specified
        if module_name is None:
            frame = inspect.currentframe()
            caller = frame.f_back if frame else None
            module_name = caller.f_globals.get('__name__', '__main__') if caller else '__main__'

        module = None  # type: Optional[ModuleType]

        # 1. Try to find the module already loaded
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # 2. Try importing dynamically
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                # 3. Fallback: resolve via __spec__ for script/test contexts
                main_module = sys.modules.get('__main__')
                spec = getattr(main_module, '__spec__', None)
                if spec is not None and hasattr(spec, 'name'):
                    alt_name = getattr(spec, 'name')
                    module = sys.modules.get(alt_name, None)
                if module is None:
                    logging.warning('get_class(): module not found: %s', module_name)
                    return None

        # 4. Retrieve the class
        class_inst = getattr(module, class_name, None)
        if class_inst is None:
            logging.debug('get_class(): class not found: %s in %s', class_name, module_name)
            return None
        if not inspect.isclass(class_inst):
            logging.debug('get_class(): "%s" found in %s but is not a class.', class_name, module_name)
            return None

        return class_inst

    # ---------------------------------------------------------------------------

    def markdown_convert(self, md):
        """Return HTML of the given markdown content.

        :param md: (str) A standard-limited markdown content
        :return: (str) The HTML content

        """
        if len(HTML) > 0:
            logging.warning(f"Markdown to HTML conversion is disabled: {HTML}")
            return ""
        return self.markdowner.convert(md)

    # ---------------------------------------------------------------------------

    def markdown_to_html(self, content):
        """Turn a markdown content into HTML.

        :param content: (str) A complex markdown content
        :return: (str) The HTML content

        """
        if len(HTML) > 0:
            logging.warning(f"Markdown to HTML conversion is disabled: {HTML}")
            return ""

        h = list()
        code = list()
        md = list()
        i = 0
        all_lines = content.split("\n")
        while i < len(all_lines):
            line = all_lines[i]

            # a new code block
            if line.strip().startswith("```") is True:
                has_language = len(line.strip()) == 3
                if len(md) > 0:
                    h.append(self.markdowner.convert("\n".join(md)))
                    md = list()
                line = ""
                while line.strip().startswith("```") is False:
                    code.append(line)
                    i = i + 1
                    if i >= len(all_lines):
                        break
                    line = all_lines[i]

                if len(code) > 0:
                    if has_language is True:
                        h.append("<pre>")
                        h.append("\n".join(code))
                        h.append("</pre>")
                    else:
                        h.append(pygments_highlight("\n".join(code), self.lexer, self.formatter))
                    code = list()
            else:
                idx = self.__is_code(line)
                if idx != -1:
                    # a code part is starting or is continued.
                    if len(md) > 0:
                        h.append(self.markdowner.convert("\n".join(md)))
                        md = list()
                    if idx > 0:
                        code.append(line[idx:])
                    else:
                        code.append(line)
                else:
                    if len(code) > 0:
                        h.append(pygments_highlight("\n".join(code), self.lexer, self.formatter))
                        code = list()
                    md.append(line)
            i = i + 1

        if len(code) > 0:
            h.append(pygments_highlight("\n".join(code), self.lexer, self.formatter))
        if len(md) > 0:
            h.append(self.markdowner.convert("\n".join(md)))

        html_result = "\n".join(h)
        return html_result.replace("<p></p>", "")

    # -----------------------------------------------------------------------

    @staticmethod
    def __is_code(line):
        entry = line.strip()
        if entry.startswith(">>>") is True:
            return line.index(">") - 1
        if entry.startswith("> ") is True:
            return line.index(">") - 1

        return -1

    # -----------------------------------------------------------------------

    def source_to_html(self, source):
        """Turn a source code content into HTML.

        :param source: (str) The source code content
        :return: (str) The HTML content

        """
        if len(HTML) > 0:
            logging.warning("Source code to HTML conversion is disabled: {:s}".format(HTML))
            return ""
        return pygments_highlight(source, self.lexer, self.formatter)
