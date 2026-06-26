# syntax=docker/dockerfile:1
#
# Multi-stage build for skillspector-quality.
#
# skillspector is not on PyPI, so it is installed from a local checkout that the
# Makefile stages into ./.docker-build/skillspector before building (the build
# context cannot reach ../SkillRater on its own). Build via `make docker-build`,
# not a bare `docker build`.

# --- builder: install everything into a self-contained venv ------------------
FROM python:3.13-slim@sha256:af5bd286051a06b38587d30a8638958f4a2f38381aa80fe859c740af3411bd4d AS builder

# uv for fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:0.5.21 /uv /uvx /bin/
ENV UV_LINK_MODE=copy

# Build deps (fallback if a dependency lacks a wheel, e.g. yara-python).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv PATH="/opt/venv/bin:$PATH"

# Install the pinned skillspector first (its source is staged by the Makefile).
COPY .docker-build/skillspector /src/skillspector
RUN uv pip install /src/skillspector

# Install skillspector-quality.
COPY pyproject.toml README.md /src/app/
COPY src /src/app/src
RUN uv pip install /src/app

# --- runtime: copy only the venv, no build tools -----------------------------
FROM python:3.13.3-slim@sha256:5cc3361b5df0f3af709d5bb6c387361d9b2262ea4155dae6c701a2f66eb73b67 AS runtime

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd -m -u 1001 appuser
USER appuser

WORKDIR /work

# Run a scan by mounting a skill directory, e.g.:
#   docker run --rm -v "$PWD/my-skill:/work/skill:ro" skillspector-quality scan /work/skill
ENTRYPOINT ["python", "-m", "skillspector_quality"]
CMD ["--help"]
