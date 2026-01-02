[github_release]: https://img.shields.io/github/release/the-citto/pytest-checkers.svg?logo=github&logoColor=white&color=orange
[pypi_version]: https://img.shields.io/pypi/v/pytest-checkers.svg?logo=python&logoColor=white
[python_versions]: https://img.shields.io/pypi/pyversions/pytest-checkers.svg?logo=python&logoColor=white
[github_license]: https://img.shields.io/github/license/the-citto/pytest-checkers.svg?logo=github&logoColor=white
[coverage]: ./docs/coverage.svg
[tox_tests]: https://github.com/the-citto/pytest-checkers/actions/workflows/tox-tests.yml/badge.svg
<!-- [github_action_tests]: https://github.com/the-citto/culting/actions/workflows/tests.yml/badge.svg -->

[![GitHub Release][github_release]](https://github.com/the-citto/pytest-checkers/releases/)
[![PyPI Version][pypi_version]](https://pypi.org/project/pytest-checkers/)
[![Python Versions][python_versions]](https://pypi.org/project/pytest-checkers/)
[![License][github_license]](https://github.com/the-citto/pytest-checkers/blob/master/LICENSE)
[![Coverage][coverage]](https://github.com/the-citto/pytest-checkers/)
[![Tox tests][tox_tests]](https://github.com/the-citto/pytest-checkers/actions/workflows/tox-tests.yml)
![PyPI - Downloads](https://img.shields.io/pypi/dm/pytest-checkers)
<br>


<figure style="display: inline-block;">
  <img src="https://github.com/the-citto/pytest-checkers/raw/main/docs/the-power-of-exponential-growth-a-story-about-knowledge.jpg" width="200" style="vertical-align: top;">
</figure>

# pytest-checkers

Use desired LSPs, type checkers, linters, and formatters (diff only).

Available optional dependencies:

`pytest_checkers[black,isort,flake8,mypy,pyright,ruff,ty]`

either of the above, or

`pytest_checkers[all]`

Simple flags: `--ruff` `--mypy` etc. or just `--checkers` for all the dependencies installed. 

Use `pyproject.toml` (and `.flake8` until they finally decide to move)
for your preferred settings for every tool.


## Note

pyright installs `pyright[nodejs]`

isort install `isort[colors]`

## Kudos

All of them are somewhat different from what I wanted and made here:

[pytest-black](https://github.com/coherent-oss/pytest-black)

[pytest-isort](https://github.com/stephrdev/pytest-isort)

[pytest-flake8](https://github.com/coherent-oss/pytest-flake8)

[pytest-mypy](https://github.com/realpython/pytest-mypy)

[pytest-pyright](https://github.com/RobertCraigie/pytest-pyright)

[pytest-ruff](https://github.com/businho/pytest-ruff)

[pytest-ty](https://github.com/boidolr/pytest-ty)

