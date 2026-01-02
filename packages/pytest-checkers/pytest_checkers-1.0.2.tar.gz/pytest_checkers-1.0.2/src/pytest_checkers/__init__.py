"""Init."""

from __future__ import annotations

import importlib.metadata
import typing

__version__ = importlib.metadata.version(__name__)

Group = typing.Literal["checkers"]
Tool = typing.Literal["black", "flake8", "isort", "mypy", "pyright", "ruff", "ty"]
EscTable = typing.Literal[
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "purple",
    "cyan",
    "white",
    "Black",
    "Red",
    "Green",
    "Yellow",
    "Blue",
    "Purple",
    "Cyan",
    "White",
    "bold",
    "light",
    "blink",
    "invert",
]

GROUP_NAME: Group = "checkers"
HELPS: dict[Tool | Group, str] = {
    "checkers": "Enable all available checks",
    "black": "Enable `black --diff`",
    "isort": "Enable `isort --diff`",
    "flake8": "Enable `flake8`",
    "ruff": "Enable `ruff check`",
    "mypy": "Enable `mypy`",
    "ty": "Enable `ty check`",
    "pyright": "Enable `pyright`",
}
