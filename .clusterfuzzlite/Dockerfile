# Pinned by digest, not by tag: a tag is mutable, so `:latest` would let the contents of this
# build change without any commit here (OpenSSF Scorecard: Pinned-Dependencies).
# Digest resolved from gcr.io/oss-fuzz-base/base-builder-python:latest.
# Dependabot's docker ecosystem keeps it current — see .github/dependabot.yml. Do not replace
# this with a bare tag; refresh the digest instead.
FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:8476df732bcde364e001aa74b5df836ca28ff9c6acefb170cd9fb34ab07feea7

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
