"""Checkers."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import typing

import pytest

from pytest_checkers import (
    GROUP_NAME,
    HELPS,
)

if typing.TYPE_CHECKING:

    from _pytest._code.code import (
        TerminalRepr,
        TracebackStyle,
    )
    from _pytest.terminal import TerminalReporter

    from pytest_checkers import (
        EscTable,
        Tool,
    )


class PluginItem(pytest.Item):
    """PluginItem."""

    def runtest(self) -> None:
        """Run test."""
        plugin = self.config.pluginmanager.get_plugin(self.name)
        if not isinstance(plugin, CheckersPlugin):  # pragma: no cover
            pytest.exit(f"Internal Error: {self.name} plugin not found during runtest")
        plugin.run_tool()
        if plugin.is_error:
            fail_msg = f"{self.name} failed with output:\n{plugin.cmd_output}"
            raise pytest.fail(fail_msg)

    def repr_failure(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
        style: TracebackStyle | None = None,
    ) -> str | TerminalRepr:
        """Repr failure."""
        _ = excinfo, style
        return f"{self.name} failed with output..."

    def reportinfo(self) -> tuple[os.PathLike[str] | str, int | None, str]:
        """Report info."""
        return self.path, 0, f"tool::{self.name}"


class CheckersPlugin:
    """Checkers plugin."""

    tool: Tool
    header_markup: EscTable
    finish_msg: str = ""

    def __init__(self, config: pytest.Config) -> None:
        """Init."""
        self.config = config
        self.cmd_output = ""
        self.cmd_returncode = 0

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return []

    @property
    def env_vars(self) -> dict[str, str]:
        """Environment variables."""
        env_vars = os.environ.copy()
        env_vars["FORCE_COLOR"] = "1"
        env_vars["MYPY_FORCE_COLOR"] = "1"
        return env_vars

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return self.cmd_returncode != 0

    def run_tool(self) -> None:
        """Run tool."""
        project_root = self.config.rootpath
        cmd = [sys.executable, "-m", self.tool, *self.cmd_flags, str(project_root)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env_vars)  # noqa: S603
        self.cmd_output = result.stdout + result.stderr
        self.cmd_returncode = result.returncode

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        """Pytest terminal summary."""
        # circumventing mypy quirk - https://github.com/python/mypy/issues/10023
        header_markup_kwarg = {typing.cast("str", self.header_markup): True}
        terminalreporter.write_sep(title=f"tests {self.tool}", sep="=", **header_markup_kwarg)
        terminalreporter.write(self.cmd_output + self.finish_msg)

    def pytest_collection_modifyitems(
        self,
        session: pytest.Session,
        config: pytest.Config,
        items: list[pytest.Item],
    ) -> None:
        """Pytest collection modify item."""
        _ = config
        item = PluginItem.from_parent(  # pyright: ignore[reportUnknownMemberType]
            session,
            name=self.tool,
        )
        item._nodeid = f"{GROUP_NAME}::{self.tool}"  # pyright: ignore[reportPrivateUsage]  # noqa: SLF001
        items.append(item)


class PyrightPlugin(CheckersPlugin):
    """Pyright plugin."""

    tool = "pyright"
    header_markup = "yellow"


class TyPlugin(CheckersPlugin):
    """Ty plugin."""

    tool = "ty"
    header_markup = "yellow"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]


class MypyPlugin(CheckersPlugin):
    """Mypy plugin."""

    tool = "mypy"
    header_markup = "blue"


class RuffPlugin(CheckersPlugin):
    """Ruff plugin."""

    tool = "ruff"
    header_markup = "purple"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["check"]


class Flake8Plugin(CheckersPlugin):
    """Flake8 plugin."""

    tool = "flake8"
    header_markup = "purple"
    finish_msg = "All done.\n"

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--color=always"]


class BlackPlugin(CheckersPlugin):
    """Black plugin."""

    tool = "black"
    header_markup = "cyan"

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output or "fail to reformat" in self.cmd_output

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        return ["--diff", "--color"]


class IsortPlugin(CheckersPlugin):
    """Isort plugin."""

    tool = "isort"
    header_markup = "cyan"
    finish_msg = "All done.\n"

    @property
    def is_error(self) -> bool:
        """Tool-specific error logic."""
        return "@@" in self.cmd_output

    @property
    def cmd_flags(self) -> list[str]:
        """Command flags."""
        if importlib.util.find_spec("colorama") is None:  # pragma: no cover  # tested with tox isortnocolor
            return ["--diff"]
        return ["--diff", "--color"]


tools_map: dict[Tool, type[CheckersPlugin]] = {
    "black": BlackPlugin,
    "flake8": Flake8Plugin,
    "isort": IsortPlugin,
    "mypy": MypyPlugin,
    "pyright": PyrightPlugin,
    "ruff": RuffPlugin,
    "ty": TyPlugin,
}
added_options: list[Tool] = []


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add CLI options."""
    group = parser.getgroup(GROUP_NAME)
    for tool, help_ in HELPS.items():
        if tool == GROUP_NAME:
            group.addoption(f"--{tool}", action="store_true", help=help_)
        elif importlib.util.find_spec(tool):
            group.addoption(f"--{tool}", action="store_true", help=help_)
            added_options.append(tool)


def pytest_configure(config: pytest.Config) -> None:
    """Get CLI selections."""
    for tool in added_options:
        if config.option.checkers:
            setattr(config.option, tool, True)
        if getattr(config.option, tool, False):
            tool_cls = tools_map[tool]
            config.pluginmanager.register(tool_cls(config), name=tool)
