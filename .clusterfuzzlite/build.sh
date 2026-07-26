#!/bin/bash -eu

# --require-hashes: every artifact pip resolves must match a digest in requirements.txt, so a
# substituted or unpinned package fails the build instead of entering the fuzzing image.
python3 -m pip install --require-hashes -r /src/.clusterfuzzlite/requirements.txt

# --no-build-isolation: use the hatchling installed above rather than letting pip fetch an
# unpinned build backend from PyPI while building the local source tree.
# --ignore-requires-python: the base image ships an older interpreter than the package pins.
python3 -m pip install /src --no-deps --no-build-isolation --ignore-requires-python

# The base image ships Python 3.11 while the package targets >=3.12, so 3.12-only syntax
# (e.g. PEP 701 f-strings) parses locally but not here. PyInstaller reacts to an unparseable
# module by silently omitting it, producing a fuzz target that dies at import with a
# confusing ModuleNotFoundError. Compile the installed package first so the real SyntaxError
# surfaces here, naming the file and line.
python3 -m compileall -q "$(python3 -c 'import os, skillspector_quality as m; print(os.path.dirname(m.__file__))')"

compile_python_fuzzer \
  /src/fuzz/fuzz_scorers.py \
  --hidden-import=skillspector_quality.quality.scorers
