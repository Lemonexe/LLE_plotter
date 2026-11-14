#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")/.."
uv sync --locked
uv run --locked scripts/build.py
