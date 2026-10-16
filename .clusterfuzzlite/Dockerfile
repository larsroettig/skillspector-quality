# Pinned by digest, not by tag: a tag is mutable, so `:latest` would let the contents of this
# build change without any commit here (OpenSSF Scorecard: Pinned-Dependencies).
# Digest resolved from gcr.io/oss-fuzz-base/base-builder-python:latest.
# Dependabot's docker ecosystem keeps it current — see .github/dependabot.yml. Do not replace
# this with a bare tag; refresh the digest instead.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:21f6fab17ace4dc76e1c56de91ee95d3d03da021df94b41056ba036f6c6f55e9

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
