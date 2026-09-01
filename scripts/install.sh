#!/bin/bash
set -euo pipefail

case "$(uname -m)" in
  arm64|aarch64) BUILD_SYS="arm64" ;;
  x86_64|amd64) BUILD_SYS="amd64" ;;
  *) BUILD_SYS="$(uname -m)" ;;
esac
echo "Build system: ${BUILD_SYS}"

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3.12 || command -v python3.11 || command -v python3)}"
"${PYTHON_BIN}" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e '.[test]'
