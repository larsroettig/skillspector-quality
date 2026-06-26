#!/bin/bash -eu

python3 -m pip install atheris
python3 -m pip install /src

compile_python_fuzzer /src/fuzz/fuzz_scorers.py
