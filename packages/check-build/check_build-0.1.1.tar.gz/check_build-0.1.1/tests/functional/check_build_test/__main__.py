# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Run a couple of functional tests for a `check-build` implementation."""

from __future__ import annotations

import dataclasses
import functools
import logging
import pathlib
import shlex
import shutil
import subprocess  # noqa: S404
import sys
import typing

import click


if typing.TYPE_CHECKING:
    from typing import Final


@dataclasses.dataclass(frozen=True)
class Config:
    """Runtime configuration for the test framework."""

    log: logging.Logger
    """The logger to send diagnostic and informational messages to."""

    program: list[str]
    """The program to test."""

    topdir: pathlib.Path
    """The path to the top-level source directory of the `check-build` project."""


def pshlex_join(words: list[str | pathlib.Path]) -> str:
    """Invoke `shlex.join()` on the stringified words."""
    return shlex.join(str(word) for word in words)


@functools.lru_cache(maxsize=2)
def build_logger(*, verbose: bool) -> logging.Logger:
    """Build a logger that outputs messages to the standard output stream."""
    name_prefix = "" if verbose else "non-"
    logger = logging.getLogger(f"check-build/{name_prefix}verbose")
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(stream=sys.stdout)
    stdout_handler.addFilter(lambda record: record.levelno == logging.INFO)
    stdout_handler.setLevel(logging.INFO)
    logger.addHandler(stdout_handler)

    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    if verbose:
        stderr_handler.addFilter(lambda record: record.levelno != logging.INFO)
        stderr_handler.setLevel(logging.DEBUG)
    else:
        stderr_handler.setLevel(logging.WARNING)
    logger.addHandler(stderr_handler)

    return logger


def assert_none(path: pathlib.Path) -> None:
    """Make sure there is nothing at that path."""
    if path.is_symlink() or path.exists():
        sys.exit(f"Did not expect {path} to exist")


def assert_file(path: pathlib.Path) -> None:
    """Make sure there is a regular file at that path."""
    if path.is_symlink() or not path.is_file():
        sys.exit(f"Expected a regular file at {path}")


def assert_dir(path: pathlib.Path) -> None:
    """Make sure there is a directory at that path."""
    if path.is_symlink() or not path.is_dir():
        sys.exit(f"Expected a directory at {path}")


def assert_no_lines(needle: str, lines: list[str]) -> None:
    """Make sure no lines contain the specified substring."""
    found: Final = [line for line in lines if needle in line]
    if found:
        sys.exit(f"Expected no lines to contain {needle!r}, got {found!r}")


def assert_lines_match(  # noqa: PLR0912
    cfg: Config,
    needle: str,
    following: list[str],
    lines: list[str],
) -> None:
    """Find the substring in a line, get the directory name, find lines that refer to it."""
    dirname: str | None = None
    next_following: str | None = following.pop(0)

    cfg.log.debug("Looing for %(needle)r in the check-build output", {"needle": needle})
    for line in lines:
        match line.partition(needle):
            case [_, middle, suffix] if middle == needle:
                if dirname is None:
                    dirname = suffix
                    cfg.log.debug("  - found temp path %(dirname)s", {"dirname": dirname})
                    cfg.log.debug("  - looking for %(next)r now", {"next": next_following})
                else:
                    sys.exit(f"Did not expect to find two lines containing {needle!r}")

            case _ if next_following is not None:
                match line.partition(next_following):
                    case [_, middle, suffix] if middle == next_following:
                        cfg.log.debug("  - found %(next)r", {"next": next_following})
                        if dirname is None:
                            sys.exit(
                                f"Did not expect to find {next_following!r} before {needle!r}",
                            )
                        elif suffix != dirname:
                            sys.exit(f"Expected '{next_following}{dirname}', got {line!r}")
                        elif following:
                            next_following = following.pop(0)
                            cfg.log.debug("  - looking for %(next)r now", {"next": next_following})
                        else:
                            next_following = None
                            cfg.log.debug("  - found everything we wanted")

                    case _:
                        # Just make sure we don't find the needle again
                        pass

            case _:
                # Just make sure we don't find the needle again
                pass

    if next_following is not None:
        sys.exit(f"Could not find {next_following!r} in the lines following {needle!r}")


def test_c_programs(cfg: Config) -> None:
    """Run `check-build` against `c/programs.toml`, analyze its output."""
    skip_both: Final = shutil.which("cc") is None
    skip_make: Final = skip_both or shutil.which("make") is None

    programs_cfg: Final = cfg.topdir / "c" / "programs.toml"
    triv_cc_prog: Final = programs_cfg.parent / "triv-cc" / "triv"
    triv_make_prog: Final = programs_cfg.parent / "triv-make" / "triv"

    def source_dir_pristine() -> None:
        """Make sure the source directories are there and not touched."""
        cfg.log.info("Making sure the source directory is as expected")

        assert_file(programs_cfg)

        assert_dir(triv_cc_prog.parent)
        assert_none(triv_cc_prog)

        assert_dir(triv_make_prog.parent)
        assert_none(triv_make_prog)

    source_dir_pristine()

    cmd: Final[list[str | pathlib.Path]] = [*cfg.program, "-v", "-c", programs_cfg]
    cfg.log.info("Invoking `%(cmd)s`", {"cmd": pshlex_join(cmd)})
    lines: Final = subprocess.check_output(cmd, cwd=cfg.topdir, encoding="UTF_8").splitlines()  # noqa: S603

    source_dir_pristine()

    if skip_both:
        assert_no_lines("Building triv-cc in ", lines)
    else:
        assert_lines_match(
            cfg,
            "Building triv-cc in ",
            ["Testing triv-cc in ", "Successfully built and run triv-cc in "],
            lines,
        )

    if skip_make:
        assert_no_lines("Building triv-make in ", lines)
    else:
        assert_lines_match(
            cfg,
            "Building triv-make in ",
            ["Testing triv-make in ", "Successfully built and run triv-make in "],
            lines,
        )

        assert_lines_match(
            cfg,
            "triv-make: About to build triv in ",
            [
                "triv-make: Making sure triv was built in ",
                "triv-make: Found triv in ",
                "triv-make: About to run triv in ",
                "triv-make: Ran triv in ",
            ],
            lines,
        )


def find_topdir(path: pathlib.Path) -> pathlib.Path:
    """Check whether the `check-build` project's top directory looks like we expect it to."""
    assert_file(path / "REUSE.toml")
    assert_dir(path / "c")
    return path


@click.command(name="check-build-test")
@click.option(
    "--topdir",
    "-d",
    type=click.Path(file_okay=False, dir_okay=True, path_type=pathlib.Path, resolve_path=True),
    default=pathlib.Path.cwd().parent,
    help="the top-level source directory of the check-build project",
)
@click.argument("program", type=str, nargs=-1, required=True)
def main(*, program: list[str], topdir: pathlib.Path) -> None:
    """Run functional tests for a check-build implementation."""
    cfg: Final = Config(log=build_logger(verbose=True), program=program, topdir=find_topdir(topdir))

    test_c_programs(cfg)


if __name__ == "__main__":
    main()
