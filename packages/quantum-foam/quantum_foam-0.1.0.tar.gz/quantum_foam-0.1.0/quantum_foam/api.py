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


"""Perform conversions between versioning schemas."""

import re

from packaging.version import VERSION_PATTERN, InvalidVersion
from packaging.version import Version as PyPI
from semver.version import Version as Semver


def _check_prefixed_version(candidate_tag: str) -> str:
    """Check if a candidate version tag is prefixed by "v".

    As SemVer specification is strict and disavows usage of prefixed versions,
    candidate tags must be cleaned before being parsed.
    """  # noqa: DOC201
    if candidate_tag.casefold().startswith("v"):
        return candidate_tag.lstrip("vV")

    return candidate_tag


def convert_to_semver(candidate_tag: str) -> str:
    """Convert a candidate tag to its equivalent semantic version.

    Parameters
    ----------
    candidate_tag : str
        A string with a possible version tag to be converted.

    Returns
    -------
    str
        The string for the candidate tag in semantic version notation.

    Raises
    ------
    InvalidVersion
        If the provided string can not be converted to SemVer.
    """
    clean_tag = _check_prefixed_version(candidate_tag)

    try:
        return str(Semver.parse(clean_tag))

    except ValueError:
        msg = f'"{clean_tag}" is not a valid semantic version'
        raise InvalidVersion(msg) from None


def convert_to_pypi(candidate_tag: str) -> str:
    """Convert a candidate tag to the PyPI version specifier.

    Parameters
    ----------
    candidate_tag : str
        A string with a possible version tag to be converted.

    Returns
    -------
    str
        The string for the candidate tag in the PyPI-compliant schema.

    Raises
    ------
    InvalidVersion
        If the provided string can not be converted to the PyPI version specifier.
    """
    try:
        return str(PyPI(candidate_tag))

    except InvalidVersion:
        msg = f'"{candidate_tag}" does not adhere to the PyPI version specifier'
        raise InvalidVersion(msg) from None


def _get_version_stage(pre: str | None, post: str | None, dev: str | None) -> str:
    """Determine the version stage from version components.

    Parameters
    ----------
    pre : str, None
        Pre-release identifier obtained from the PyPI version (e.g., "a", "b", "rc").
    post : str, None
        Post-release identifier.
    dev : str, None
        Development release identifier.

    Returns
    -------
    str
        The version stage name.
    """
    # Map pre-release identifiers to stage names
    pre_release_map = {"a": "alpha", "b": "beta", "rc": "pre-release"}

    if pre in pre_release_map:
        return pre_release_map[pre]

    if post is not None:
        return "post-release"

    if dev is not None:
        return "development"

    return "release"


def extract_pvi(candidate_tag: str) -> str:
    """Extract the Package Version Identifier (PVI) from a candidate tag.

    Parameters
    ----------
    candidate_tag : str
        A string with a possible version tag.

    Returns
    -------
    str
        The version stage identifier.
    """
    r = re.compile(VERSION_PATTERN, re.VERBOSE)
    pypi_version = convert_to_pypi(candidate_tag)

    match = r.match(pypi_version).groupdict()  # type: ignore[union-attr]

    return _get_version_stage(
        match.get("pre_l"), match.get("post_l"), match.get("dev_l")
    )
