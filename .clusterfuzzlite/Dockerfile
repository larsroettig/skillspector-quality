# Pinned by digest, not by tag: a tag is mutable, so `:latest` would let the contents of this
# build change without any commit here (OpenSSF Scorecard: Pinned-Dependencies).
# Digest resolved from gcr.io/oss-fuzz-base/base-builder-python:latest.
# Dependabot's docker ecosystem keeps it current — see .github/dependabot.yml. Do not replace
# this with a bare tag; refresh the digest instead.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:bfd6d19416d9f7a791857d3f5746bc9050138a1843aa7e98b617469d8d631bab

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
