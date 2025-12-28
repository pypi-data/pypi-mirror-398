# The MIT License (MIT)
# Copyright (c) 2025 The Galactipy Contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
# OR OTHER DEALINGS IN THE SOFTWARE.


"""Specify Rich styles to render text output in the terminal.

Themes defined in this module can be added to the `AppCustomStyles` class and used in
conjunction with `rich.console.Console` to override the default terminal theme.

See https://rich.readthedocs.io/en/stable/style.html#style-themes for more information.

"""

from dataclasses import dataclass

from rich.theme import Theme

# Noctis VS Code theme text colours, full colorscheme definition at:
# https://github.com/liviuschera/noctis
NOCTIS_THEME = Theme(
    {
        "string": "#49e9a6",
        "fstring": "#16b673",
        "comment": "#5b858b",
        "function": "#16a6b6",
        "method": "#49d6e9",
        "standout": "#49ace9",
        "number": "#7060eb",
        "keyword": "#df769b",
        "declaration": "#e66533",
        "property": "#d67e5c",
        "constant": "#d5971a",
        "variable": "#e4b781",
        "bold string": "bold #49e9a6",
        "bold fstring": "bold #16b673",
        "bold comment": "bold #5b858b",
        "bold function": "bold #16a6b6",
        "bold method": "bold #49d6e9",
        "bold standout": "bold #49ace9",
        "bold number": "bold #7060eb",
        "bold keyword": "bold #df769b",
        "bold declaration": "bold #e66533",
        "bold property": "bold #d67e5c",
        "bold constant": "bold #d5971a",
        "bold variable": "bold #e4b781",
    }
)


@dataclass(frozen=True)
class AppCustomThemes:
    """Define custom Rich themes for console output with Quantum Foam."""

    NOCTIS: Theme = NOCTIS_THEME
