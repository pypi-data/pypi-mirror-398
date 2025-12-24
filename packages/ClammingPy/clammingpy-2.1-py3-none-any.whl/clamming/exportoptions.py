"""
:filename: clamming.exportoptions.py
:author: Brigitte Bigi
:contact: contact@sppas.org
:summary: Store the options and content for an export.

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
import logging

# ---------------------------------------------------------------------------


class ExportOptions:
    """Store the options and content for an export to documented files.

    ExportOptions is a data class, used to store options and content for
    exporting a documented file. It provides methods to set and get various
    information such as software name, copyright, icon, title, favicon, and
    theme. It also allows setting the names of the next and previous classes
    or modules for generating a table of contents (HTML only).

    :example:
    >>> h = ExportOptions()
    >>> h.software = "Clamming"
    >>> h.theme = "light"
    >>> html_head = h.get_head()
    >>> html_nav = h.get_nav()
    >>> html_footer = h.get_footer()

    """

    # ----------------------------------------------------------------------------
    # Public Constants
    # ----------------------------------------------------------------------------

    HTML_HEAD = \
        """
        <head>
            
            <title>{TITLE}</title>

            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes" />
            <meta name="description" content="{META_DESCRIPTION}" />

            <link rel="logo icon" href="{STATICS}/{FAVICON}" />
            <link rel="stylesheet" href="{WEXA_STATICS}/css/wexa.css" type="text/css" />
            <link rel="stylesheet" href="{WEXA_STATICS}/css/layout.css" type="text/css" />
            <link rel="stylesheet" href="{WEXA_STATICS}/css/book.css" type="text/css" />
            <link rel="stylesheet" href="{WEXA_STATICS}/css/menu.css" type="text/css" />
            <link rel="stylesheet" href="{WEXA_STATICS}/css/code.css" type="text/css" />
            <link rel="stylesheet" href="{STATICS}/clamming.css" type="text/css" />

            <!-- Whakerexa JS loader: ES6 modules on http(s), bundle on file:// -->
            <script>
            (function () {{
              const usingFile = (window.location.protocol === 'file:');
              const s = document.createElement('script');
            
              if (usingFile) {{
                s.src = '{WEXA_STATICS}/js/wexa.bundle.js';
              }} else {{
                s.type = 'module';
                s.src = '{WEXA_STATICS}/js/wexa.js';
              }}
            
              s.onload = function () {{
                window.Wexa.onload.addLoadFunction(function () {{
                  const book = new window.Wexa.Book("main-content");
                  book.fill_table(false);
                }});
              }};
            
              document.head.appendChild(s);
            }})();
            </script>

       </head>
       
       """

    HTML_BUTTONS_ACCESSIBILITY = \
        """
            <a role="button" class="skip" href="#main-content" aria-label="Go to main content">
                Go to main content
            </a>
            <nav>
                <ul>
                    <li>
                        <button id="btn-contrast" role="menuitem" class="print-off" onclick="window.Wexa.accessibility.switch_contrast_scheme()" aria-label="Contrast">
                            <img class="nav-item-img" src="{WEXA_STATICS}/icons/contrast_switcher.jpg" alt="Contrast" id="img-contrast"/>
                        </button>
                    </li>
                    <li>
                        <button id="btn-theme" class="print-off" role="menuitem" onclick="window.Wexa.accessibility.switch_color_scheme()" aria-label="Theme" >
                            <img class="nav-item-img" src="{WEXA_STATICS}/icons/theme_switcher.png" alt="Theme" id="img-theme"/>
                        </button>
                    </li>
                </ul>
            </nav>
        """
    HTML_FOOTER = \
        """
            <footer>
                <p class="copyright">{COPYRIGHT}</p>
            </footer>
        """

    # ----------------------------------------------------------------------------
    # Customized HTML information
    # ----------------------------------------------------------------------------

    # About the documented software
    DEFAULT_SOFTWARE = ""
    DEFAULT_COPYRIGHT = ""
    DEFAULT_ICON = ""
    DEFAULT_URL = ""

    # For creating HTML pages
    DEFAULT_WEXA_STATICS = "./wexa_statics"
    DEFAULT_STATICS = "./statics"
    DEFAULT_TITLE = ""
    DEFAULT_FAVICON = "clamming32x32.ico"
    DEFAULT_THEME = "light"

    # ----------------------------------------------------------------------------

    def __init__(self):
        """Create a documentation export system for a ClamsPack.

        Main functionalities:

        - Store options and content for exporting a standalone file;
        - Set and get HTML information such as software name, copyright, icon, title, favicon, and theme;
        - Set the names of the next and previous classes or modules for generating a table of contents.

        """
        self.__readme = True

        # HTML information
        self.__software = ExportOptions.DEFAULT_SOFTWARE
        self.__copyright = ExportOptions.DEFAULT_COPYRIGHT
        self.__url = ExportOptions.DEFAULT_URL
        self.__icon = ExportOptions.DEFAULT_ICON
        self.__title = ExportOptions.DEFAULT_TITLE
        self.__favicon = ExportOptions.DEFAULT_FAVICON
        self.__theme = ExportOptions.DEFAULT_THEME
        self.__statics = ExportOptions.DEFAULT_STATICS
        self.__wexa_statics = ExportOptions.DEFAULT_WEXA_STATICS
        self.__descr = "Python class documentation"

        # Previous and next class and module names for the TOC
        self.__next_class = None
        self.__prev_class = None
        self.__next_pack = None
        self.__prev_pack = None

    # ----------------------------------------------------------------------------

    def get_add_readme(self) -> bool:
        """Return whether the README of library is added or not."""
        return self.__readme

    def set_add_readme(self, readme: bool) -> NoReturn:
        """Set whether the README of library is added or not.

        :param readme: (bool) whether the README is added or not.

        """
        self.__readme = bool(readme)

    readme = property(get_add_readme, set_add_readme)

    # ----------------------------------------------------------------------------

    def get_software(self) -> str:
        """Return the name of the software."""
        return self.__software

    def set_software(self, name: str = DEFAULT_SOFTWARE) -> NoReturn:
        """Set a software name.

        :param name: (str) Name of the documented software
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.software. Got {} instead."
                            "".format(name))
        self.__software = name

    software = property(get_software, set_software)

    # ----------------------------------------------------------------------------

    def get_url(self) -> str:
        """Return the url of the software."""
        return self.__url

    def set_url(self, name: str = "") -> NoReturn:
        """Set a software url.

        :param name: (str) URL of the documented software
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.url. Got {} instead."
                            "".format(name))
        self.__url = name

    url = property(get_url, set_url)

    # ----------------------------------------------------------------------------

    def get_copyright(self) -> str:
        """Return the copyright of the HTML page."""
        return self.__copyright

    def set_copyright(self, text: str = DEFAULT_COPYRIGHT) -> NoReturn:
        """Set a copyright text, added to the footer of the page.

        :param text: (str) Copyright of the documented software
        :raises: TypeError: Given text is not a string

        """
        if isinstance(text, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.copyright. Got {} instead."
                            "".format(text))
        self.__copyright = text

    copyright = property(get_copyright, set_copyright)

    # ----------------------------------------------------------------------------

    def get_icon(self) -> str:
        """Return the icon filename of the software."""
        return self.__icon

    def set_icon(self, name: str = DEFAULT_ICON) -> NoReturn:
        """Set an icon filename.

        :param name: (str) Filename of the icon of the documented software
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.icon. Got {} instead."
                            "".format(name))
        self.__icon = name

    icon = property(get_icon, set_icon)

    # ----------------------------------------------------------------------------

    def get_title(self) -> str:
        """Return the title of the HTML page."""
        return self.__title

    def set_title(self, text: str = DEFAULT_TITLE) -> NoReturn:
        """Set a title to the output HTML pages.

        :param text: (str) Title of the HTML pages
        :raises: TypeError: Given text is not a string

        """
        if isinstance(text, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.title. Got {} instead."
                            "".format(text))
        self.__title = text

    title = property(get_title, set_title)

    # ----------------------------------------------------------------------------

    def get_statics(self) -> str:
        """Return the static path of the CSS, JS, etc."""
        return self.__statics

    def set_statics(self, name: str = DEFAULT_STATICS) -> NoReturn:
        """Set the static path of the customs CSS, JS, etc.

        :param name: (str) Path of the static elements
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.statics. Got {} instead."
                            "".format(name))
        self.__statics = name

    statics = property(get_statics, set_statics)

    # ----------------------------------------------------------------------------

    def get_wexa_statics(self) -> str:
        """Return the static path of the CSS, JS, etc. of Whakerexa. """
        return self.__wexa_statics

    def set_wexa_statics(self, name: str = DEFAULT_WEXA_STATICS) -> NoReturn:
        """Set the static path of the customs CSS, JS, etc. of Whakerexa.

        :param name: (str) Path of the static elements
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.wexa_statics. Got {} instead."
                            "".format(name))
        self.__wexa_statics = name

    wexa_statics = property(get_wexa_statics, set_wexa_statics)

    # ----------------------------------------------------------------------------

    def get_favicon(self) -> str:
        """Return the favicon filename of the HTML pages."""
        return self.__favicon

    def set_favicon(self, name: str = DEFAULT_FAVICON) -> NoReturn:
        """Set a favicon to the output HTML pages.

        :param name: (str) Favicon of the HTML pages
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.favicon. Got {} instead."
                            "".format(name))
        self.__favicon = name

    favicon = property(get_favicon, set_favicon)

    # ----------------------------------------------------------------------------

    def get_theme(self) -> str:
        """Return the theme of the HTML page."""
        return self.__theme

    def set_theme(self, name: str = DEFAULT_THEME) -> NoReturn:
        """Set a theme name.

        :param name: (str) Name of the theme of the HTML pages
        :raises: TypeError: Given name is not a string

        """
        if isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.theme. Got {} instead."
                            "".format(name))
        self.__theme = name

    theme = property(get_theme, set_theme)

    # ----------------------------------------------------------------------------

    def get_description(self) -> str:
        """Return the 160 chars description of the HTML page."""
        return self.__theme

    def set_description(self, descr: str = "") -> NoReturn:
        """Set a 160 chars max description text.

        :param descr: (str) Description of the documented document
        :raises: TypeError: Given descr is not a string

        """
        if isinstance(descr, (str, bytes)) is False:
            raise TypeError("Expected a 'str' for the HTMLDocExport.descr. Got {} instead."
                            "".format(descr))
        descr = descr.replace("\n", " ")
        descr = descr.replace("'", " ")
        descr = descr.replace('"', " ")
        if len(descr) < 90:
            logging.warning(f"Given description is a little bit shorted than the 90 expected characters: {descr}")
            descr = "Python Class Documentation of " + descr
        if len(descr) > 160:
            logging.warning(f"Given description is longer than 160 characters: {descr}.")
        self.__descr = descr[:160]

    description = property(get_description, set_description)

    # ----------------------------------------------------------------------------

    def get_next_class(self) -> str:
        """Return the name of the next documented class."""
        return self.__next_class

    def set_next_class(self, name: str | None = None) -> NoReturn:
        """Set the name of the next documented class.

        :param name: (str|None) Name of the next documented class
        :raises: TypeError: Given name is not a string

        """
        if name is not None and isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' or None for the HTMLDocExport.next_class. Got {} instead."
                            "".format(name))
        self.__next_class = name

    next_class = property(get_next_class, set_next_class)

    # ----------------------------------------------------------------------------

    def get_prev_class(self) -> str:
        """Return the name of the previous documented class, for the ToC."""
        return self.__prev_class

    def set_prev_class(self, name: str | None = None) -> NoReturn:
        """Set the name of the previous documented class.

        :param name: (str|None) Name of the previous documented class
        :raises: TypeError: Given name is not a string

        """
        if name is not None and isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' or None for the HTMLDocExport.prev_class. "
                            "Got {} instead.".format(name))
        self.__prev_class = name

    prev_class = property(get_prev_class, set_prev_class)

    # ----------------------------------------------------------------------------

    def get_next_module(self) -> str:
        """Return the name of the next documented module."""
        return self.__next_pack

    def set_next_module(self, name: str | None = None) -> NoReturn:
        """Set the name of the next documented module.

        :param name: (str|None) Name of the next documented module
        :raises: TypeError: Given name is not a string

        """
        if name is not None and isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' or None for the HTMLDocExport.next_module. "
                            "Got {} instead.".format(name))
        self.__next_pack = name

    next_module = property(get_next_module, set_next_module)

    # ----------------------------------------------------------------------------

    def get_prev_module(self) -> str:
        """Return the name of the previous documented module, for the ToC."""
        return self.__prev_pack

    def set_prev_module(self, name: str | None = None) -> NoReturn:
        """Set the name of the previous documented module.

        :param name: (str|None) Name of the previous documented module
        :raises: TypeError: Given name is not a string

        """
        if name is not None and isinstance(name, (str, bytes)) is False:
            raise TypeError("Expected a 'str' or None for the HTMLDocExport.prev_module. "
                            "Got {} instead.".format(name))
        self.__prev_pack = name

    prev_module = property(get_prev_module, set_prev_module)

    # ----------------------------------------------------------------------------
    # Export of the HTML contents
    # ----------------------------------------------------------------------------

    def get_head(self) -> str:
        """Return the HTML 'head' of the page."""
        return ExportOptions.HTML_HEAD.format(
            TITLE=self.__title,
            FAVICON=self.__favicon,
            THEME=self.__theme,
            STATICS=self.__statics,
            WEXA_STATICS=self.__wexa_statics,
            META_DESCRIPTION=self.__descr
        )

    # ----------------------------------------------------------------------------

    def get_header(self) -> str:
        """Return the 'header' of the HTML->body of the page."""
        h = list()
        h.append("    <header>")
        h.append(ExportOptions.HTML_BUTTONS_ACCESSIBILITY.format(WEXA_STATICS=self.__wexa_statics))
        if len(self.__software) > 0:
            h.append("    <h1>{SOFTWARE}</h1>".format(SOFTWARE=self.__software))
        if len(self.__icon) > 0:
            h.append('        <p><img class="small-logo" src="{STATICS}/{ICON}" '
                     'alt="Software logo"/></p>'.format(STATICS=self.__statics, ICON=self.__icon))
        if len(self.__url) > 0:
            h.append('        <p><a class="external-link" href="{URL}">{URL}</a></p>'.format(URL=self.__url))
        h.append("    </header>")
        return "\n".join(h)

    # ----------------------------------------------------------------------------

    def get_nav(self) -> str:
        """Return the 'nav' of the HTML->body of the page."""
        nav = list()
        nav.append("<nav id=\"nav-book\" class=\"side-nav\">")
        if self.__software == ExportOptions.DEFAULT_SOFTWARE:
            nav.append("    <h1>Documentation</h1>")
        else:
            nav.append("    <h1>{SOFTWARE}</h1>".format(SOFTWARE=self.__software))
        if len(self.__icon) > 0:
            nav.append("    <img class=\"small-logo center\" src=\"{STATICS}/{ICON}\" alt=\"\"/>"
                       "".format(STATICS=self.__statics, ICON=self.__icon))
        if len(self.__url) > 0:
            nav.append('        <p><a class="external-link" href="{URL}">{URL}</a></p>'.format(URL=self.__url))
        nav.append("    <ul>")
        nav.append(ExportOptions.__nav_link("&crarr; Prev. Module", self.__prev_pack))
        nav.append(ExportOptions.__nav_link("&uarr; Prev. Class", self.__prev_class))
        nav.append(ExportOptions.__nav_link("&#8962; Index", "index.html"))
        nav.append(ExportOptions.__nav_link("&darr; Next Class", self.__next_class))
        nav.append(ExportOptions.__nav_link("&rdsh; Next Module", self.__next_pack))
        nav.append("    </ul>")
        nav.append("    <h2>Table of Contents</h2>")
        nav.append("    <ul id=\"toc\"></ul>")
        nav.append("    <hr>")
        nav.append("    <p><small>Automatically created</small></p><p><small>by <a class=\"external-link\" href=\"https://clamming.sf.net\">ClammingPy</a></small></p>")
        nav.append("</nav>")
        return "\n".join(nav)

    # -----------------------------------------------------------------------

    def get_footer(self) -> str:
        """Return the 'footer' of the HTML->body of the page."""
        return ExportOptions.HTML_FOOTER.format(COPYRIGHT=self.__copyright)

    # -----------------------------------------------------------------------
    # Private
    # -----------------------------------------------------------------------

    @staticmethod
    def __nav_link(text: str, link: str | None) -> str:
        if link is None:
            a = 'aria-disabled="true"'
        else:
            a = 'href="{:s}"'.format(link)
        return """<li><a role="button" tabindex="0" {LINK}> {TEXT}</a></li>""".format(LINK=a, TEXT=text)
