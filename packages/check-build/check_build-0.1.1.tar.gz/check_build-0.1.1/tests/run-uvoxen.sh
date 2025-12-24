#!/bin/sh
# SPDX-FileCopyrightText: Peter Pentchev <roam@ringlet.net>
# SPDX-License-Identifier: BSD-2-Clause

set -e

: "${UV:=uv}"
: "${UVOXEN:=uvoxen}"

run()
{
	rm -rf -- .venv

	echo "Running $UVOXEN with the default Python version"
	"$UVOXEN" uv run

	"$UVOXEN" -p supported uv run -e mypy,unit-tests,functional

	echo "Using $UV to restore the virtual environment for the default Python version"
	rm -rf -- .venv
	"${UV}" sync --exact
}

run
