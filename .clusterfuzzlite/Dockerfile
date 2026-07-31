# Pinned by digest, not by tag: a tag is mutable, so `:latest` would let the contents of this
# build change without any commit here (OpenSSF Scorecard: Pinned-Dependencies).
# Digest resolved from gcr.io/oss-fuzz-base/base-builder-python:latest.
# Dependabot's docker ecosystem keeps it current — see .github/dependabot.yml. Do not replace
# this with a bare tag; refresh the digest instead.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:6b2b3a7e4a2da50de47f94925cffbe34747e1aae4f33d7f07ba6c681dd648b23

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
