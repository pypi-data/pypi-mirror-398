# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause
"""Test the check-build library's utility functions."""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING
from unittest import mock

from check_build import util as cb_util


if TYPE_CHECKING:
    from typing import IO


def test_build_logger() -> None:
    """Test that build_logger() outputs things as it should."""
    res = []
    wanted_streams = {sys.stdout, sys.stderr}

    def mock_emit(self: logging.StreamHandler[IO[str]], record: logging.LogRecord) -> None:
        """Record messages that actually make it out to the streams we follow."""
        if self.stream not in wanted_streams:
            return

        res.append((self.stream, record.levelno, record.getMessage()))

    lverbose = cb_util.build_logger(verbose=True)
    with mock.patch("logging.StreamHandler.emit", new=mock_emit):
        lverbose.debug("d 1")
        lverbose.info("i 1")
        lverbose.error("e 1")

    assert res == [
        (sys.stderr, logging.DEBUG, "d 1"),
        (sys.stdout, logging.INFO, "i 1"),
        (sys.stderr, logging.ERROR, "e 1"),
    ]
    res.clear()

    lnonverbose = cb_util.build_logger(verbose=False)
    with mock.patch("logging.StreamHandler.emit", new=mock_emit):
        lnonverbose.debug("d 2")
        lnonverbose.info("i 2")
        lnonverbose.error("e 2")

    assert res == [(sys.stdout, logging.INFO, "i 2"), (sys.stderr, logging.ERROR, "e 2")]
    res.clear()

    with mock.patch("logging.StreamHandler.emit", new=mock_emit):
        lverbose.debug("d 3")
        lverbose.info("i 3")
        lverbose.error("e 3")

    assert res == [
        (sys.stderr, logging.DEBUG, "d 3"),
        (sys.stdout, logging.INFO, "i 3"),
        (sys.stderr, logging.ERROR, "e 3"),
    ]
    res.clear()
