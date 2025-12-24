# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the functionality with a trivial configuration."""

from __future__ import annotations

import pathlib
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from check_build import defs
from check_build import parse
from check_build import process
from check_build import util


if TYPE_CHECKING:
    from typing import Final


TOPDIR = pathlib.Path(__file__).parent.parent.parent.parent

PROG_NAME_TRIVIAL = "triv-make"
PROG_NAME_NO_SUCH = "no such program"

PROG_CC = "cc"
PROG_MAKE = "make"

CMD_MAKE_ALL = [PROG_MAKE]
CMD_MAKE_TEST = [PROG_MAKE, "test"]


@pytest.mark.parametrize(
    ("force", "which_result", "expected_which", "expected_commands"),
    [
        (False, {PROG_CC, PROG_MAKE}, [PROG_CC, PROG_MAKE], [CMD_MAKE_ALL, CMD_MAKE_TEST]),
        (False, {PROG_CC}, [PROG_CC, PROG_MAKE], []),
        (True, {PROG_CC, PROG_MAKE}, [PROG_CC, PROG_MAKE], [CMD_MAKE_ALL, CMD_MAKE_TEST]),
        (True, {PROG_CC}, [PROG_CC, PROG_MAKE], [CMD_MAKE_ALL, CMD_MAKE_TEST]),
    ],
)
def test_trivial(
    *,
    force: bool,
    which_result: set[str],
    expected_which: list[str],
    expected_commands: list[list[str | pathlib.Path]],
) -> None:
    """Parse the configuration, find the 'triv-make' test, run it."""
    which: list[str] = []
    commands: list[list[str | pathlib.Path]] = []

    def mock_run(
        cmd: list[str | pathlib.Path],
        *,
        check: bool = False,
        cwd: pathlib.Path | None = None,
        shell: bool = False,
    ) -> None:
        """Mock subprocess.run(), check for the right programs in the right order."""
        assert check
        assert not shell

        assert cwd is not None
        assert cwd.is_dir()
        assert cwd != TOPDIR / "c/triv-make"

        commands.append(cmd)

    def mock_which(prog: str) -> str | None:
        """Mock subprocess.run(), check for the right programs in the right order."""
        which.append(prog)
        return f"/weird/path/{prog}" if prog in which_result else None

    cfg: Final = parse.load_config(
        config=TOPDIR / "c/programs.toml",
        force=force,
        programs=(PROG_NAME_TRIVIAL,),
        logger=util.build_logger(verbose=True),
    )
    assert PROG_NAME_TRIVIAL in cfg.program
    assert PROG_NAME_NO_SUCH not in cfg.program
    assert all(isinstance(prog, defs.Program) for prog in cfg.program.values())
    assert cfg.selected == [PROG_NAME_TRIVIAL]

    with mock.patch("subprocess.run", new=mock_run), mock.patch("shutil.which", new=mock_which):
        if expected_commands:
            process.build_and_test(cfg, PROG_NAME_TRIVIAL)
        else:
            with pytest.raises(defs.SkippedProgramError) as err_info:
                process.build_and_test(cfg, PROG_NAME_TRIVIAL)
            assert err_info.value.prog == PROG_NAME_TRIVIAL

    assert which == expected_which
    assert commands == expected_commands
