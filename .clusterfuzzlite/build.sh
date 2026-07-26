#!/bin/bash -eu

# --require-hashes: every artifact pip resolves must match a digest in requirements.txt, so a
# substituted or unpinned package fails the build instead of entering the fuzzing image.
python3 -m pip install --require-hashes -r /src/.clusterfuzzlite/requirements.txt

# --no-build-isolation: use the hatchling installed above rather than letting pip fetch an
# unpinned build backend from PyPI while building the local source tree.
# --ignore-requires-python: the base image ships an older interpreter than the package pins.
python3 -m pip install /src --no-deps --no-build-isolation --ignore-requires-python

compile_python_fuzzer \
  /src/fuzz/fuzz_scorers.py \
  --hidden-import=skillspector_quality.quality.scorers
