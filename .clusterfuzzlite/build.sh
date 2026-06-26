#!/bin/bash -eu

python3 -m pip install -r /src/.clusterfuzzlite/requirements.txt
python3 -m pip install /src --no-deps

compile_python_fuzzer /src/fuzz/fuzz_scorers.py
