#!/bin/bash
# generate Python stub file

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

ROOT_DIR="$(pwd)"
DEFAULT_PYTHON="$ROOT_DIR/.venv/bin/python"
PYTHON_BIN="${PYTHON_BIN:-$DEFAULT_PYTHON}"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "Failed to locate Python executable: $PYTHON_BIN" >&2
    exit 1
fi

PYTHONHOME="$($PYTHON_BIN - <<'PY'
import sys
from pathlib import Path

print(Path(sys.base_prefix).resolve())
PY
)"

if [ -z "$PYTHONHOME" ]; then
    echo "Failed to resolve PYTHONHOME" >&2
    exit 1
fi

PYO3_PYTHON="$PYTHON_BIN" \
PYTHONHOME="$PYTHONHOME" \
cargo run --bin stub_gen --features stub_gen
