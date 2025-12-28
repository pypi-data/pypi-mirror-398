# Quantum Foam

<div align="center">

<!-- Project details -->
[![Python support][badge1]][burl1]
[![PyPI Release][badge1a]][burl1]
[![Repository][badge2]][burl2]
[![Releases][badge3]][burl3]
[![Licence][blic1]][blic2]
[![Expand your project structure from atoms of code to galactic dimensions.][badge4]][burl4]

<!-- Information on development -->
[![Project type][badge5]][burl5]
[![Project stage][badge6]][burl6]
[![Contributions Welcome][badge7]][burl7]
[![Open issues][badge8]][burl8]
[![Merge Requests][badge9]][burl9]

<!-- Styling policies -->
[![Code style: Ruff][badge10]][burl10]
[![Docstrings][bdocstr1]][bdocstr2]
[![Gitmoji][badge11]][burl11]
[![Semantic Line Breaks][badge12]][burl12]

<!-- Development utilities -->
[![Poetry][badge13]][burl13]
[![Pre-commit][badge14]][burl14]
[![Bandit][badge15]][burl15]
[![isort][badge16]][burl16]
[![Editorconfig][badge17]][burl17]

<!-- Quality assurance -->
[![Intended Effort Versioning][badge18]][burl18]
[![Code Quality][bqa1]][bqa2]
[![Coverage][badge19]][burl19]
[![Pipelines][badge20]][burl20]

_Simple and minimal version tag converter_

---

**POWERED BY**

[![Powered by Typer][btyper]][ltyper]

</div>

## :sunrise_over_mountains: Purpose & Function

This is a simple command-line utility
to convert between different versioning schemes,
including:

- [SemVer][purpose1];
- [PyPI Version Specifier][purpose2].

Quantum Foam provides minimal functionality,
making it ideal to be used
in CI/CD pipelines.

## :inbox_tray: Installation

Use [`pipx`][install1] to install Quantum Foam
in an isolated environment:

```bash
pipx install quantum-foam
```

Then you can run it from the command line:

```bash
quantum-foam --help
```

## :black_joker: How to Use It

The top-level command
is the entry point
for additional
operations:

> _`quantum-foam [--version | -v]`_
>> **`--version`**
>>
>> **`-v`**
>>
>> Print
>> the current version of the program
>> and exit.

The subcommands
convert the provided tag
to the respective versioning schema
being requested:

> _`quantum-foam pypi TAG`_
>> **`TAG`**
>>
>> A candidate tag version
>> to convert.

> _`quantum-foam semver TAG`_
>> **`TAG`**
>>
>> A candidate tag version
>> to convert.

## :reminder_ribbon: Contributing

There are several ways
to contribute to Quantum Foam.
Refer to our [`CONTRIBUTING` guide][burl7]
for all relevant details.

Currently,
we are seeking help
to tackle areas of focus
that are more pressing
to our project's progress
and would make an immediate difference
in helping us achieve our [mission][contributing1].

Here are some key contributions
your can help us with
right now:

- Provide input in [design discussions][contributing2]
  to define the desired features of Quantum Foam.
<!-- DEFINE additional areas of assistance as development progresses -->

## :ship: Releases

You can see
the list of available releases
on the [GitLab Releases][release1] page.

We follow [Intended Effort Versioning][release2] specification,
details can be found in our [`CONTRIBUTING` guide][burl18].

## :shield: Licence

[![Licence][blic1]][blic2]

This project is licenced
under the terms of the **MIT License**.
See [LICENCE][blic2] for more details.

## :page_with_curl: Citation

We provide a [`CITATION.cff`][cite1] file
to make it easier to cite this project
in your paper.

## Credits [![Expand your project structure from atoms of code to galactic dimensions.][badge4]][burl4]

This project was generated with [Galactipy][burl4].

<!-- Anchors -->

[badge1]: https://img.shields.io/pypi/pyversions/quantum-foam?style=for-the-badge
[badge1a]: https://img.shields.io/pypi/v/quantum-foam?style=for-the-badge&logo=pypi&color=3775a9
[badge2]: https://img.shields.io/badge/GitLab-0B2640?style=for-the-badge&logo=gitlab&logoColor=white
[badge3]: https://img.shields.io/gitlab/v/release/galactipy%2Futilities%2Fquantum-foam?style=for-the-badge&logo=semantic-release&color=253747
[badge4]: https://img.shields.io/badge/made%20with-galactipy%20%F0%9F%8C%8C-179287?style=for-the-badge&labelColor=193A3E
[badge5]: https://img.shields.io/badge/project%20type-toy-blue?style=for-the-badge
[badge6]: https://img.shields.io/pypi/status/quantum-foam?style=for-the-badge&logo=theplanetarysociety&label=stage
[badge7]: https://img.shields.io/static/v1.svg?label=Contributions&message=Welcome&color=0059b3&style=for-the-badge
[badge8]: https://img.shields.io/gitlab/issues/open/galactipy%2Futilities%2Fquantum-foam?style=for-the-badge&color=fca326
[badge9]: https://img.shields.io/gitlab/merge-requests/open/galactipy%2Futilities%2Fquantum-foam?style=for-the-badge&color=6fdac9
[badge10]: https://img.shields.io/badge/code%20style-ruff-261230?style=for-the-badge&labelColor=grey
[badge11]: https://img.shields.io/badge/%F0%9F%98%9C_gitmoji-ffdd67?style=for-the-badge
[badge12]: https://img.shields.io/badge/sembr-FF6441?style=for-the-badge&logo=apmterminals&logoColor=white
[badge13]: https://img.shields.io/endpoint?url=https://python-poetry.org/badge/v0.json&style=for-the-badge
[badge14]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
[badge15]: https://img.shields.io/badge/security-bandit-yellow?style=for-the-badge
[badge16]: https://img.shields.io/badge/imports-isort-1674b1?style=for-the-badge&labelColor=ef8336
[badge17]: https://img.shields.io/badge/Editorconfig-E0EFEF?style=for-the-badge&logo=editorconfig&logoColor=000
[badge18]: https://img.shields.io/badge/effver-0097a7?style=for-the-badge&logo=semver
[badge19]: https://img.shields.io/codacy/coverage/9f83256084244c9ab54252c596d68494?style=for-the-badge&logo=codacy
[badge20]: https://img.shields.io/gitlab/pipeline-status/galactipy%2Futilities%2Fquantum-foam?branch=master&style=for-the-badge&logo=gitlab&logoColor=white&label=master

[burl1]: https://pypi.org/project/quantum-foam/
[burl2]: https://gitlab.com/galactipy/utilities/quantum-foam
[burl3]: https://gitlab.com/galactipy/utilities/quantum-foam/-/releases
[burl4]: https://kutt.it/7fYqQl
[burl5]: https://project-types.github.io/#toy
[burl6]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/ROADMAP.md#development-stages
[burl7]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md
[burl8]: https://gitlab.com/galactipy/utilities/quantum-foam/-/issues
[burl9]: https://gitlab.com/galactipy/utilities/quantum-foam/-/merge_requests
[burl10]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md#codestyle
[burl11]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md#commit-customs
[burl12]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md#semantic-line-breaks
[burl13]: https://python-poetry.org/
[burl14]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/.pre-commit-config.yaml
[burl15]: https://bandit.readthedocs.io/en/latest/
[burl16]: https://pycqa.github.io/isort/
[burl17]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/.editorconfig
[burl18]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md#versioning-customs
[burl19]: https://app.codacy.com/gl/galactipy/utilities/quantum-foam/coverage
[burl20]: https://gitlab.com/galactipy/utilities/quantum-foam/-/pipelines

[blic1]: https://img.shields.io/gitlab/license/galactipy/utilities/quantum-foam?style=for-the-badge
[blic2]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/LICENCE

[bqa1]: https://img.shields.io/codacy/grade/9f83256084244c9ab54252c596d68494?style=for-the-badge&logo=codacy
[bqa2]: https://app.codacy.com/gl/galactipy/utilities/quantum-foam/dashboard

[btyper]: https://img.shields.io/badge/Typer-black?style=for-the-badge&logo=typer
[ltyper]: https://typer.tiangolo.com/
[borbittings]: https://img.shields.io/badge/orbittings-007A68?style=for-the-badge&logo=orbittings
[lorbittings]: https://gitlab.com/galactipy/orbittings

[purpose1]: https://semver.org/
[purpose2]: https://packaging.python.org/en/latest/specifications/version-specifiers/

[install1]: https://pipx.pypa.io/latest/installation/

[contributing1]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/ROADMAP.md#project-mission
[contributing2]: https://gitlab.com/galactipy/utilities/quantum-foam/-/issues?state=opened&label_name%5B%5D=design%3A%3A%2A&type%5B%5D=issue

[release1]: https://gitlab.com/galactipy/utilities/quantum-foam/-/releases
[release2]: https://jacobtomlinson.dev/effver/

[bdocstr1]: https://img.shields.io/badge/docstrings-numpydoc-4dabcf?style=for-the-badge&labelColor=4d77cf
[bdocstr2]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CONTRIBUTING.md#docstring-convention

[cite1]: https://gitlab.com/galactipy/utilities/quantum-foam/-/blob/master/CITATION.cff
