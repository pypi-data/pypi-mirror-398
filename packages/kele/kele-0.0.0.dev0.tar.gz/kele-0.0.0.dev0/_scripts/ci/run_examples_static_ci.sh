#!/usr/bin/env bash
set -euo pipefail

WORKDIR="${1:?workdir required}"
LOGFILE="${2:?logfile required}"

pushd "$WORKDIR" >/dev/null

uv sync
uv run maturin develop --skip-install

set +e
uv run python examples/static.py 2>&1 | tee "${GITHUB_WORKSPACE}/${LOGFILE}"
code=${PIPESTATUS[0]}
set -e

popd >/dev/null

exit "$code"
