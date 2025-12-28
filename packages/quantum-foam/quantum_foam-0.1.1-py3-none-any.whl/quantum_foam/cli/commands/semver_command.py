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


"""Return the semantic version for a candidate version tag."""

from typing import Annotated

import typer
from rich import print as rich_print

from quantum_foam import convert_to_semver

semver_app = typer.Typer(rich_markup_mode="rich")


@semver_app.command()
def semver(
    tag: Annotated[
        str, typer.Argument(help=":bookmark: A candidate tag version to convert.")
    ],
) -> None:
    """:input_numbers: Convert a candidate tag to its SemVer equivalent."""
    rich_print(convert_to_semver(tag))
