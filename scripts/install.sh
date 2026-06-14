#!/usr/bin/env bash
#
# Install skillspector-quality and its (unpublished) skillspector dependency, using uv.
#
# skillspector is not on PyPI, so it must be installed editable from a local
# checkout BEFORE this package. This script:
#   1. creates a .venv with a compatible Python (>=3.12,<3.14 — skillspector
#      forbids 3.14; uv fetches the interpreter if needed),
#   2. installs skillspector editable from a local checkout,
#   3. verifies the version matches the pin in pyproject.toml,
#   4. installs skillspector-quality (with dev extras).
#
# Requires uv (https://docs.astral.sh/uv/).
#
# Usage:
#   scripts/install.sh [SKILLSPECTOR_SRC]
#
#   SKILLSPECTOR_SRC  Path to the skillspector checkout.
#                     Default: ../SkillRater (sibling of this repo).
#                     May also be set via the SKILLSPECTOR_SRC env var.
#
# Examples:
#   scripts/install.sh
#   scripts/install.sh ../SkillRater
#   SKILLSPECTOR_SRC=/path/to/skillspector scripts/install.sh

set -euo pipefail

# --- locate repo root (parent of this script's dir) --------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# --- require uv --------------------------------------------------------------
if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv not found. Install it: https://docs.astral.sh/uv/getting-started/" >&2
  echo "       e.g. curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# --- resolve the skillspector source path ------------------------------------
SKILLSPECTOR_SRC="${1:-${SKILLSPECTOR_SRC:-${REPO_ROOT}/../SkillRater}}"
if [ ! -f "${SKILLSPECTOR_SRC}/pyproject.toml" ]; then
  echo "ERROR: no skillspector checkout at '${SKILLSPECTOR_SRC}'" >&2
  echo "       Pass the path as an argument or set SKILLSPECTOR_SRC." >&2
  exit 1
fi
SKILLSPECTOR_SRC="$(cd "${SKILLSPECTOR_SRC}" && pwd)"

# --- create the venv with a compatible Python (uv fetches it if missing) -----
echo ">> Creating .venv (Python >=3.12,<3.14) with uv"
uv venv .venv --python 3.13 || uv venv .venv --python 3.12
# shellcheck disable=SC1091
source .venv/bin/activate
echo ">> Using $(python --version 2>&1)"

# --- install skillspector (editable) -----------------------------------------
echo ">> Installing skillspector (editable) from ${SKILLSPECTOR_SRC}"
uv pip install -e "${SKILLSPECTOR_SRC}"

# --- verify version against the pin in pyproject.toml ------------------------
PINNED="$(grep -oE 'skillspector==[0-9][0-9A-Za-z.\-]*' pyproject.toml | head -1 | cut -d= -f3 || true)"
INSTALLED="$(python -c 'import importlib.metadata as m; print(m.version("skillspector"))')"
echo ">> skillspector installed: ${INSTALLED} (pinned: ${PINNED:-unpinned})"
if [ -n "${PINNED}" ] && [ "${PINNED}" != "${INSTALLED}" ]; then
  echo "WARNING: checkout version ${INSTALLED} != pin ${PINNED}." >&2
  echo "         Check out skillspector ${PINNED}, or update the pin in pyproject.toml." >&2
fi

# --- install this package (with dev extras) ----------------------------------
echo ">> Installing skillspector-quality (editable, dev extras)"
uv pip install -e '.[dev]'

echo
echo "Done. Activate the venv and run:"
echo "  source .venv/bin/activate"
echo "  python -m skillspector_quality scan ./my-skill/"
