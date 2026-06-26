FROM gcr.io/oss-fuzz-base/base-builder-python@sha256:8dfd24ae037974085ebfe0abebd540d9e3587b514574cf0289844a16fc3c2de3

COPY . $SRC/
COPY .clusterfuzzlite/build.sh $SRC/build.sh

WORKDIR $SRC/
