# Pinned by digest, not by tag: a tag is mutable, so `:latest` would let the contents of this
# build change without any commit here (OpenSSF Scorecard: Pinned-Dependencies).
# Digest resolved from gcr.io/oss-fuzz-base/base-builder-python:latest.
# Dependabot's docker ecosystem keeps it current — see .github/dependabot.yml. Do not replace
# this with a bare tag; refresh the digest instead.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:1de9e4ac301ddea42b8846480d5e4903580ed5071357c9173a4d26a4af65a6fa

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
